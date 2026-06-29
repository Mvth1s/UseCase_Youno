"""
Module de collecte : normalisation d'URL, fetch HTTP et extraction du contenu HTML.

Responsabilite unique : fournir aux modules aval (tech_detector, gtm_detector,
profiler) les donnees brutes issues du fetch d'une page web. Aucune logique de
detection ou d'inference ici.
"""

from __future__ import annotations

import re
from typing import TypedDict
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# Constantes de configuration
# ---------------------------------------------------------------------------

# Texte visible tronque a ce nombre de caracteres pour le Profiler LLM
VISIBLE_TEXT_MAX_LENGTH: int = 3000

# Nombre maximum de liens collectes (evite les pages tres denses)
MAX_INTERNAL_LINKS: int = 50
MAX_EXTERNAL_LINKS: int = 20

# Timeout HTTP global (connexion + lecture) en secondes
HTTP_TIMEOUT: int = 10

# Nombre maximum de redirections suivies
MAX_REDIRECTS: int = 5

# User-agent realiste pour eviter les blocages basiques anti-bot
USER_AGENT: str = "Mozilla/5.0 (compatible; KonsoleBot/1.0; +https://konsole.ai)"


# ---------------------------------------------------------------------------
# Schema de sortie
# ---------------------------------------------------------------------------


class ScrapedData(TypedDict):
    """
    Donnees brutes extraites d'une page web.

    Ce dict est le seul format accepte par les modules de detection aval.
    Chaque champ est toujours present ; les valeurs manquantes sont "" ou None.
    """

    url: str                          # URL originale apres normalisation du schema
    final_url: str                    # URL reelle apres suivi de redirections
    status_code: int                  # Code HTTP de la reponse finale
    html: str                         # HTML brut complet de la page
    page_title: str                   # Contenu de la balise <title>
    meta_description: str             # Contenu de <meta name="description">
    og_title: str                     # Open Graph og:title
    og_description: str               # Open Graph og:description
    og_image: str | None              # Open Graph og:image (None si absent)
    favicon_url: str | None           # URL absolue du favicon (None si introuvable)
    internal_links: list[str]         # Liens vers le meme domaine (max 50)
    external_links: list[str]         # Liens vers des domaines tiers (max 20)
    lang: str                         # Attribut lang de la balise <html>
    response_headers: dict[str, str]  # Headers HTTP de la reponse (cles en minuscules)
    visible_text: str                 # Texte visible nettoye, tronque a 3000 chars


# ---------------------------------------------------------------------------
# Fonctions utilitaires privees
# ---------------------------------------------------------------------------


def _normalize_url(raw_url: str) -> str:
    """
    Normalise une URL brute en URL valide avec schema https par defaut.

    Accepte : 'stripe.com', 'www.stripe.com', 'https://stripe.com', 'http://stripe.com'.

    Args:
        raw_url: URL brute saisie par l'utilisateur ou l'API.

    Returns:
        URL normalisee avec schema.

    Raises:
        ValueError: si l'URL est vide, sans domaine ou contient des caracteres illegaux.
    """
    url = raw_url.strip()
    if not url:
        raise ValueError("L'URL fournie est vide.")

    # Ajouter le schema HTTPS si aucun schema n'est present
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # Un netloc vide signifie qu'aucun domaine n'a ete detecte
    if not parsed.netloc:
        raise ValueError(
            f"URL invalide : aucun domaine detecte dans '{raw_url}'. "
            "Exemple valide : 'stripe.com' ou 'https://stripe.com'."
        )

    # Rejeter les espaces et caracteres de controle dans le domaine
    if re.search(r"[\s\x00-\x1f\x7f]", parsed.netloc):
        raise ValueError(
            f"URL invalide : caracteres illegaux detectes dans le domaine '{parsed.netloc}'."
        )

    return url


def _extract_og_tag(soup: BeautifulSoup, property_name: str) -> str:
    """
    Extrait la valeur d'une balise Open Graph.

    Args:
        soup: arbre BeautifulSoup de la page.
        property_name: nom de la propriete OG (ex. 'og:title').

    Returns:
        Valeur de la propriete, ou chaine vide si absente.
    """
    tag = soup.find("meta", attrs={"property": property_name})
    if isinstance(tag, Tag):
        content = tag.get("content")
        if isinstance(content, str):
            return content.strip()
    return ""


def _extract_favicon(soup: BeautifulSoup, base_url: str) -> str | None:
    """
    Detecte l'URL du favicon en cherchant les balises <link> appropriees.
    Retourne le /favicon.ico par defaut si aucune balise n'est trouvee.

    Args:
        soup: arbre BeautifulSoup de la page.
        base_url: URL de base pour resoudre les chemins relatifs.

    Returns:
        URL absolue du favicon, ou None si la detection echoue.
    """
    # Priorites des relations de favicon (ordre decroissant de preference)
    priority_rels = ["icon", "shortcut icon", "apple-touch-icon"]

    for rel_value in priority_rels:
        # BeautifulSoup parse l'attribut rel sous forme de liste
        tag = soup.find(
            "link",
            rel=lambda r, rv=rel_value: (
                isinstance(r, list) and rv.lower() in [x.lower() for x in r]
            ) or (
                isinstance(r, str) and rv.lower() == r.lower()
            ),
        )
        if isinstance(tag, Tag):
            href = tag.get("href")
            if isinstance(href, str) and href.strip():
                return urljoin(base_url, href.strip())

    # Favicon par defaut a la racine du domaine
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

    return None


def _extract_links(
    soup: BeautifulSoup, base_url: str
) -> tuple[list[str], list[str]]:
    """
    Extrait et classifie les liens de la page en liens internes et externes.

    Un lien est interne si son domaine (sans 'www.') correspond a celui de base_url.

    Args:
        soup: arbre BeautifulSoup de la page.
        base_url: URL de base pour resoudre les chemins relatifs.

    Returns:
        Tuple (internal_links, external_links), chaque liste limitee a son maximum.
    """
    parsed_base = urlparse(base_url)
    # Normaliser le domaine de reference (sans le 'www.' optionnel)
    base_domain = parsed_base.netloc.lstrip("www.")

    internal_links: list[str] = []
    external_links: list[str] = []
    seen_normalized: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        if not isinstance(a_tag, Tag):
            continue

        href = a_tag.get("href", "")
        if not isinstance(href, str):
            continue
        href = href.strip()

        # Ignorer les ancres, les pseudo-protocoles et les liens non-naviguables
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue

        # Resoudre les URLs relatives par rapport a la page finale
        absolute_url = urljoin(base_url, href)
        parsed_link = urlparse(absolute_url)

        # Ne conserver que les liens HTTP/HTTPS
        if parsed_link.scheme not in ("http", "https"):
            continue

        # Cle de deduplication : schema + netloc + path (sans query ni fragment)
        dedup_key = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}"
        if dedup_key in seen_normalized:
            continue
        seen_normalized.add(dedup_key)

        # Classifier selon le domaine
        link_domain = parsed_link.netloc.lstrip("www.")
        if link_domain == base_domain:
            if len(internal_links) < MAX_INTERNAL_LINKS:
                internal_links.append(absolute_url)
        else:
            if len(external_links) < MAX_EXTERNAL_LINKS:
                external_links.append(absolute_url)

    return internal_links, external_links


def _extract_visible_text(soup: BeautifulSoup) -> str:
    """
    Extrait le texte visible de la page apres suppression des balises non-textuelles.

    Attention : cette fonction modifie le BeautifulSoup en place (decompose).
    Elle doit etre appelee en DERNIER parmi les extractions sur un meme soup.

    Args:
        soup: arbre BeautifulSoup de la page (sera modifie).

    Returns:
        Texte nettoye, tronque a VISIBLE_TEXT_MAX_LENGTH caracteres.
    """
    # Supprimer les elements non-textuels ou non-pertinents pour le LLM
    for tag in soup(
        ["script", "style", "noscript", "head", "meta", "link", "svg", "img",
         "iframe", "object", "embed", "figure"]
    ):
        tag.decompose()

    # Extraire le texte brut avec separation par espace
    raw_text = soup.get_text(separator=" ", strip=True)

    # Normaliser les espaces multiples en un seul espace
    clean_text = re.sub(r"\s+", " ", raw_text).strip()

    return clean_text[:VISIBLE_TEXT_MAX_LENGTH]


# ---------------------------------------------------------------------------
# Fonction principale publique
# ---------------------------------------------------------------------------


def scrape(url: str) -> ScrapedData:
    """
    Normalise l'URL, effectue le fetch HTTP et extrait les metadonnees de la page.

    C'est le seul point d'entree public de ce module. Les exceptions sont
    intentionnellement non-interceptees ici afin que main.py puisse les
    traduire en codes HTTP appropries (503, 400, etc.).

    Args:
        url: URL du site a analyser. Le schema est optionnel.

    Returns:
        ScrapedData: donnees brutes prates pour tech_detector, gtm_detector et profiler.

    Raises:
        ValueError: URL invalide (pas de domaine, caracteres illegaux) ou contenu non-HTML.
        httpx.TimeoutException: le site n'a pas repondu dans les 10 secondes.
        httpx.ConnectError: domaine injoignable (DNS introuvable, connexion refusee).
        httpx.HTTPStatusError: la reponse HTTP a un statut non-2xx.
        httpx.TooManyRedirects: plus de 5 redirections consecutives.
    """
    # Etape 1 : normalisation de l'URL (peut lever ValueError)
    normalized_url = _normalize_url(url)

    # Etape 2 : fetch HTTP avec httpx
    # Toutes les exceptions httpx remontent directement a l'appelant
    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        headers=headers,
    ) as client:
        response = client.get(normalized_url)

        # Lever httpx.HTTPStatusError si le code est 4xx ou 5xx
        response.raise_for_status()

        # Capturer les donnees pendant que la connexion est ouverte
        html_content: str = response.text
        final_url: str = str(response.url)
        status_code: int = response.status_code
        response_headers: dict[str, str] = dict(response.headers)
        content_type: str = response_headers.get("content-type", "")

    # Etape 3 : verifier que le contenu est du HTML
    # (evite de parser des PDFs, images, flux JSON, etc.)
    if "text/html" not in content_type.lower():
        raise ValueError(
            f"Le contenu retourne n'est pas du HTML "
            f"(Content-Type: '{content_type}'). URL: {normalized_url}"
        )

    # Etape 4 : extraction BeautifulSoup
    # html.parser est un choix robuste, disponible sans dependance systeme
    soup = BeautifulSoup(html_content, "html.parser")

    # --- Titre de la page ---
    title_tag = soup.find("title")
    page_title: str = (
        title_tag.get_text(strip=True) if isinstance(title_tag, Tag) else ""
    )

    # --- Meta description ---
    meta_desc_tag = soup.find(
        "meta", attrs={"name": re.compile(r"^description$", re.IGNORECASE)}
    )
    meta_description: str = ""
    if isinstance(meta_desc_tag, Tag):
        content = meta_desc_tag.get("content")
        if isinstance(content, str):
            meta_description = content.strip()

    # --- Balises Open Graph ---
    og_title: str = _extract_og_tag(soup, "og:title")
    og_description: str = _extract_og_tag(soup, "og:description")
    og_image_raw: str = _extract_og_tag(soup, "og:image")
    og_image: str | None = og_image_raw if og_image_raw else None

    # --- Langue de la page ---
    html_tag = soup.find("html")
    lang: str = ""
    if isinstance(html_tag, Tag):
        lang_attr = html_tag.get("lang")
        if isinstance(lang_attr, str):
            lang = lang_attr.strip()

    # --- Favicon ---
    favicon_url: str | None = _extract_favicon(soup, final_url)

    # --- Liens internes et externes ---
    internal_links, external_links = _extract_links(soup, final_url)

    # --- Texte visible (DOIT etre extrait en dernier : modifie le soup) ---
    visible_text: str = _extract_visible_text(soup)

    return ScrapedData(
        url=normalized_url,
        final_url=final_url,
        status_code=status_code,
        html=html_content,
        page_title=page_title,
        meta_description=meta_description,
        og_title=og_title,
        og_description=og_description,
        og_image=og_image,
        favicon_url=favicon_url,
        internal_links=internal_links,
        external_links=external_links,
        lang=lang,
        response_headers=response_headers,
        visible_text=visible_text,
    )
