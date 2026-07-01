"""
Module de profilage LLM : appel unique a l'API Mistral pour inferer le profil de l'entreprise.

Un seul appel LLM dans toute la chaine (contrainte de cout et de latence).
La sortie JSON est forcee via le parametre response_format et parsee defensivement.
En cas d'echec (timeout, quota, JSON malforme, cle absente), un profil partiel est renvoye
sans interrompre le reste du pipeline.

Version du prompt : 1.0
"""

from __future__ import annotations

import json
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

from app.models import CompanyProfile
from app.scraper import ScrapedData


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# URL de l'API Mistral, compatible avec le format OpenAI Chat Completions
MISTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"

# Modele utilise : bon ratio qualite/cout/latence, disponible sur le free tier
MISTRAL_MODEL: str = "mistral-small-latest"

# Timeout de l'appel HTTP vers l'API Mistral (en secondes)
MISTRAL_TIMEOUT: int = 20

# Nombre maximum de caracteres du texte visible injectes dans le prompt utilisateur
# (maitrise le budget de tokens ; les metadonnees structurees passent en tete)
PROMPT_TEXT_MAX_CHARS: int = 2000

# Version du prompt systeme — incrementer si SYSTEM_PROMPT change
PROMPT_VERSION: str = "1.1"

# Valeurs autorisees pour le champ audience
VALID_AUDIENCE_VALUES: frozenset[str] = frozenset({"B2B", "B2C", "mixed"})

# Valeurs canoniques autorisees pour le champ estimated_size (conformes au scorer)
VALID_SIZE_VALUES: frozenset[str] = frozenset({
    "startup <50",
    "PME 50-500",
    "ETI 500-5000",
    "grande entreprise >5000",
})


# ---------------------------------------------------------------------------
# Prompt systeme (versionne dans le code, lisible et modifiable)
# ---------------------------------------------------------------------------

# PROMPT VERSION 1.0
# Modifications : incrementer la version ci-dessus et noter les changements.
SYSTEM_PROMPT: str = """\
Tu es un analyste B2B specialise dans la qualification de comptes commerciaux.
A partir du contenu d'un site web, tu identifies le profil de l'entreprise.
Tu reponds UNIQUEMENT avec un objet JSON valide - aucun preambule, aucune explication, aucun bloc markdown.

Le JSON doit respecter exactement ce schema :
{
  "name": "Nom commercial de l'entreprise",
  "description": "Description en 1 a 2 phrases de ce que fait l'entreprise",
  "sector": "Secteur d'activite (ex: Fintech, SaaS RH, CRM, E-commerce, Cybersecurite...)",
  "estimated_size": "EXACTEMENT l'une de ces 4 valeurs : \"startup <50\", \"PME 50-500\", \"ETI 500-5000\", \"grande entreprise >5000\"",
  "audience": "B2B ou B2C ou mixed"
}

Regles strictes :
- "estimated_size" doit valoir EXACTEMENT l'une de ces 4 chaines (respecter la casse et la ponctuation exactes) : "startup <50", "PME 50-500", "ETI 500-5000", "grande entreprise >5000". Aucune autre valeur n'est acceptee.
- "audience" doit valoir exactement "B2B", "B2C" ou "mixed" (respecter la casse exacte).
- Si une information est incertaine, fais une estimation raisonnee plutot que de laisser vide.
- Ne jamais ajouter de champs supplementaires au schema.
- Ne jamais envelopper le JSON dans des backticks ou des balises de code.
- Reponds UNIQUEMENT avec le JSON brut, rien d'autre.
"""


# ---------------------------------------------------------------------------
# Fonctions utilitaires privees
# ---------------------------------------------------------------------------


def _get_api_key() -> str:
    """
    Recupere la cle API Mistral depuis l'environnement.

    Raises:
        RuntimeError: si MISTRAL_API_KEY est absente ou vide au demarrage.
    """
    key: str | None = os.getenv("MISTRAL_API_KEY")
    if not key or not key.strip():
        raise RuntimeError(
            "MISTRAL_API_KEY absente de l'environnement. "
            "Definir cette variable avant de lancer l'application "
            "(voir backend/.env.example)."
        )
    return key.strip()


def _build_user_prompt(data: ScrapedData) -> str:
    """
    Construit le prompt utilisateur a partir des metadonnees et du texte visible.

    Les metadonnees structurees (title, meta, og) sont injectees en tete
    pour maximiser leur signal meme si le texte visible est tronque.
    Le texte visible est limite a PROMPT_TEXT_MAX_CHARS caracteres.

    Args:
        data: donnees scrappees de la page.

    Returns:
        Prompt utilisateur pret a etre envoye a Mistral.
    """
    url_display: str = data.get("final_url") or data.get("url", "")
    title: str = data.get("page_title", "") or ""
    meta: str = data.get("meta_description", "") or ""
    og_title: str = data.get("og_title", "") or ""
    og_desc: str = data.get("og_description", "") or ""
    visible: str = data.get("visible_text", "") or ""

    # Tronquer le texte visible pour rester dans le budget de tokens Mistral
    truncated_text: str = visible[:PROMPT_TEXT_MAX_CHARS]

    lines: list[str] = ["Contenu du site web a analyser :"]

    if url_display:
        lines.append(f"URL : {url_display}")
    if title:
        lines.append(f"Titre de la page : {title}")
    if meta:
        lines.append(f"Meta description : {meta}")
    if og_title and og_title != title:
        lines.append(f"Open Graph title : {og_title}")
    if og_desc and og_desc != meta:
        lines.append(f"Open Graph description : {og_desc}")

    lines.append("")
    lines.append("Texte visible de la page :")
    lines.append(truncated_text)
    lines.append("")
    lines.append("Reponds UNIQUEMENT avec le JSON, sans markdown, sans explication.")

    return "\n".join(lines)


def _extract_domain_name(url: str) -> str:
    """
    Extrait un nom commercial lisible depuis une URL.

    Exemple : 'https://stripe.com/payments' -> 'Stripe'

    Utilise dans le fallback quand le LLM est indisponible.

    Args:
        url: URL finale de la page (avec ou sans schema).

    Returns:
        Nom capitalise extrait du domaine, ou chaine vide si l'extraction echoue.
    """
    if not url:
        return ""
    try:
        # Ajouter un schema si absent pour que urlparse fonctionne
        full_url: str = url if "://" in url else "https://" + url
        parsed = urlparse(full_url)
        hostname: str = parsed.hostname or ""
        # Supprimer le 'www.' et prendre le premier segment (nom du domaine)
        hostname = re.sub(r"^www\.", "", hostname)
        domain_root: str = hostname.split(".")[0]
        return domain_root.capitalize() if domain_root else ""
    except Exception:
        # Ne jamais propager d'exception dans une fonction utilitaire de fallback
        return ""


def _parse_llm_response(raw_content: str) -> dict:
    """
    Parse la reponse brute du LLM en dictionnaire Python.

    Strategie en trois passes pour gerer les reponses imparfaites :
    1. Parse direct du texte brut.
    2. Extraction depuis un bloc markdown (``` ... ```) via regex puis parse.
    3. Recherche d'un objet JSON quelconque dans le texte puis parse.

    Args:
        raw_content: contenu textuel brut renvoye par le LLM.

    Returns:
        Dictionnaire Python parse depuis le JSON.

    Raises:
        ValueError: si le contenu est vide.
        json.JSONDecodeError: si le contenu n'est pas parsable apres toutes les passes.
    """
    if not raw_content or not raw_content.strip():
        raise ValueError("Reponse LLM vide — aucun contenu a parser.")

    cleaned: str = raw_content.strip()

    # Passe 1 : parse direct du JSON brut (cas nominal)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Passe 2 : extraction depuis un bloc markdown ```json ... ``` ou ``` ... ```
    md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except json.JSONDecodeError:
            pass

    # Passe 3 : extraire le premier objet JSON trouvable dans le texte
    obj_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if obj_match:
        # Leve json.JSONDecodeError si toujours invalide — sera capturee par l'appelant
        return json.loads(obj_match.group(0))

    raise json.JSONDecodeError(
        "Aucun objet JSON trouvable dans la reponse LLM.",
        cleaned,
        0,
    )


def _sanitize_size(value: str) -> str:
    """
    Normalise la valeur du champ 'estimated_size' aux quatre valeurs canoniques.

    Gere les variantes renvoyees par le LLM malgre le prompt contraint :
    ex. "PME" -> "PME 50-500", "startup" -> "startup <50".
    L'ordre des tests suit la specificite decroissante pour eviter les faux positifs.

    Args:
        value: valeur brute renvoyee par le LLM.

    Returns:
        L'une des 4 valeurs canoniques de VALID_SIZE_VALUES, ou "" si non identifiable.
    """
    if not value or not value.strip():
        return ""

    stripped: str = value.strip()

    # Valeur deja canonique : court-circuit
    if stripped in VALID_SIZE_VALUES:
        return stripped

    lower: str = stripped.lower()

    # Ordre : du plus specifique au plus general pour eviter les collisions
    if "startup" in lower or "<50" in lower:
        return "startup <50"
    if "eti" in lower or "500-5000" in lower:
        return "ETI 500-5000"
    if "pme" in lower or "50-500" in lower:
        return "PME 50-500"
    if "grande" in lower or ">5000" in lower or "5000+" in lower or "large enterprise" in lower:
        return "grande entreprise >5000"

    # Valeur hors perimetre : le scorer attribuera 0 pt plutot que de scorer faussement
    logger.warning("[profiler] Valeur estimated_size non reconnue : %r — champ laisse vide.", value)
    return ""


def _sanitize_audience(value: str) -> str:
    """
    Normalise la valeur du champ 'audience' aux trois valeurs autorisees.

    Gere les variantes de casse (b2b -> B2B) et les valeurs hors perimetre
    (ex. 'both', 'b2b et b2c') qui sont ramenees a 'mixed'.

    Args:
        value: valeur brute renvoyee par le LLM.

    Returns:
        "B2B", "B2C" ou "mixed".
    """
    normalized: str = value.strip().upper()
    if normalized == "B2B":
        return "B2B"
    if normalized == "B2C":
        return "B2C"
    # Toute valeur hors perimetre est interpretee comme mixte
    return "mixed"


def _build_fallback_profile(data: ScrapedData) -> CompanyProfile:
    """
    Construit un profil partiel sans appel au LLM.

    Deduit le nom commercial du domaine et la description depuis les metadonnees
    disponibles. Les champs qui requierent une inference LLM restent vides.
    Le profil est toujours valide — jamais d'exception propagee.

    Args:
        data: donnees scrappees de la page.

    Returns:
        CompanyProfile partiel (name et description eventuellement remplis).
    """
    name: str = _extract_domain_name(data.get("final_url") or data.get("url", ""))
    # Utiliser la premiere description disponible parmi meta et og
    description: str = (
        data.get("meta_description")
        or data.get("og_description")
        or ""
    )
    return CompanyProfile(
        name=name,
        description=description,
        sector="",
        estimated_size="",
        audience="",
    )


# ---------------------------------------------------------------------------
# Fonction principale publique
# ---------------------------------------------------------------------------


def build_profile(data: ScrapedData) -> CompanyProfile:
    """
    Appelle l'API Mistral avec le contenu scrape pour produire le profil entreprise.

    Le prompt systeme force une sortie JSON stricte (name, description, sector,
    estimated_size, audience). Le parsing est defensif : tout champ manquant ou
    mal forme est remplace par la valeur par defaut de CompanyProfile.

    En cas d'echec du LLM (timeout, indisponibilite, quota, JSON malforme,
    cle absente), retourne un profil partiel sans propager d'exception.
    L'echec du LLM ne bloque jamais le reste du pipeline d'analyse.

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        CompanyProfile: profil infere (complet si succes LLM, partiel si echec).
    """

    # ------------------------------------------------------------------
    # 1. Recuperation de la cle API (echec rapide avant tout appel reseau)
    # ------------------------------------------------------------------
    try:
        api_key: str = _get_api_key()
    except RuntimeError as exc:
        logger.error("[profiler] Cle API absente ou invalide : %s — retour fallback.", exc)
        return _build_fallback_profile(data)

    # ------------------------------------------------------------------
    # 2. Construction du payload pour l'API Mistral
    # ------------------------------------------------------------------
    user_prompt: str = _build_user_prompt(data)

    payload: dict = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        # Force une reponse JSON valide cote modele (parametre Mistral/OpenAI)
        "response_format": {"type": "json_object"},
        # Faible temperature : resultats plus deterministes et reproductibles
        "temperature": 0.1,
        # Le profil JSON est court — limiter max_tokens reduit la latence et le cout
        "max_tokens": 512,
    }

    # ------------------------------------------------------------------
    # 3. Appel HTTP vers l'API Mistral
    # ------------------------------------------------------------------
    try:
        with httpx.Client(timeout=MISTRAL_TIMEOUT) as client:
            response = client.post(
                MISTRAL_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

        # Gestion explicite des codes d'erreur HTTP notables
        if response.status_code == 401:
            logger.error(
                "[profiler] Cle API Mistral invalide (HTTP 401) — retour fallback."
            )
            return _build_fallback_profile(data)

        if response.status_code == 429:
            # Quota depasse ou rate limit — non bloquant pour le reste du pipeline
            logger.warning(
                "[profiler] Quota Mistral depasse (HTTP 429) — retour fallback."
            )
            return _build_fallback_profile(data)

        if response.status_code >= 500:
            logger.error(
                "[profiler] Erreur serveur Mistral (HTTP %d) — retour fallback.",
                response.status_code,
            )
            return _build_fallback_profile(data)

        # Lever HTTPStatusError pour les autres codes non-2xx (4xx non geres ci-dessus)
        response.raise_for_status()

    except httpx.TimeoutException as exc:
        logger.error(
            "[profiler] Timeout (%ds) lors de l'appel Mistral : %s — retour fallback.",
            MISTRAL_TIMEOUT,
            exc,
        )
        return _build_fallback_profile(data)

    except httpx.ConnectError as exc:
        logger.error(
            "[profiler] Connexion a l'API Mistral impossible : %s — retour fallback.", exc
        )
        return _build_fallback_profile(data)

    except httpx.HTTPStatusError as exc:
        logger.error(
            "[profiler] Erreur HTTP Mistral (HTTP %d) : %s — retour fallback.",
            exc.response.status_code,
            exc,
        )
        return _build_fallback_profile(data)

    # ------------------------------------------------------------------
    # 4. Extraction du contenu genere depuis la reponse JSON de l'API
    # ------------------------------------------------------------------
    try:
        response_body: dict = response.json()
        choices: list = response_body.get("choices") or []

        if not choices:
            raise ValueError(
                f"Reponse Mistral sans champ 'choices'. "
                f"Body recu : {str(response_body)[:200]}"
            )

        raw_content: str = choices[0].get("message", {}).get("content", "")

        if not raw_content:
            raise ValueError("Champ 'content' vide dans la reponse Mistral.")

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.error(
            "[profiler] Structure de reponse Mistral inattendue : %s — retour fallback.", exc
        )
        return _build_fallback_profile(data)

    # ------------------------------------------------------------------
    # 5. Parsing defensif du JSON genere par le LLM
    # ------------------------------------------------------------------
    try:
        parsed: dict = _parse_llm_response(raw_content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error(
            "[profiler] JSON LLM non parsable : %s | Contenu brut (200 chars) : %.200s"
            " — retour fallback.",
            exc,
            raw_content,
        )
        return _build_fallback_profile(data)

    # ------------------------------------------------------------------
    # 6. Construction du CompanyProfile avec valeurs par defaut
    # ------------------------------------------------------------------
    raw_audience: str = parsed.get("audience", "")
    audience: str = _sanitize_audience(raw_audience) if raw_audience else ""

    raw_size: str = parsed.get("estimated_size", "")
    estimated_size: str = _sanitize_size(raw_size) if raw_size else ""

    return CompanyProfile(
        name=parsed.get("name", ""),
        description=parsed.get("description", ""),
        sector=parsed.get("sector", ""),
        estimated_size=estimated_size,
        audience=audience,
    )
