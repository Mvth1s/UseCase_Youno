"""
Module de detection des signaux Go-To-Market (GTM).

Signaux detectes par categories :
  - Outils de chat / live support (Intercom, Drift, Crisp...)
  - Pixels publicitaires (Meta Pixel, LinkedIn Insight Tag, Google Ads...)
  - Outils d'analytics (GA4, Segment, Amplitude, Mixpanel...)
  - Pages cles : pricing (signal de SaaS monetise), demo (intention commerciale),
                 careers (signal de croissance)

Logique de detection pure par signatures -- aucun LLM, aucune heuristique floue.
Chaque signal detecte est une donnee directement exploitable par une equipe sales.

Pour etendre le catalogue, ajouter une ligne dans la liste correspondante.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import GtmSignals
from app.scraper import ScrapedData


# ---------------------------------------------------------------------------
# Structure du catalogue de signatures GTM
# ---------------------------------------------------------------------------


@dataclass
class HtmlSignature:
    """
    Signature detectee par presence d'au moins un pattern dans le HTML brut.
    La comparaison est toujours insensible a la casse.
    """

    name: str
    patterns: list[str]


# ---------------------------------------------------------------------------
# Catalogue : Outils de chat et live support
# ---------------------------------------------------------------------------

_CHAT_SIGNATURES: list[HtmlSignature] = [
    HtmlSignature("Intercom",          ["widget.intercom.io", "app.intercom.com",
                                         "intercom.io/js", "intercomsettings"]),
    HtmlSignature("Drift",             ["js.drift.com", "drift.com/core.js",
                                         "driftt.com"]),
    HtmlSignature("Crisp",             ["client.crisp.chat", "crisp.chat/js",
                                         "$crisp.push"]),
    HtmlSignature("HubSpot Chat",      ["js.hs-scripts.com",
                                         "hubspot.com/conversations"]),
    HtmlSignature("Zendesk Chat",      ["static.zdassets.com", "ekr.zdassets.com"]),
    HtmlSignature("Freshchat",         ["wchat.freshchat.com",
                                         "freshchat.com/js"]),
    HtmlSignature("Tawk.to",           ["embed.tawk.to"]),
    HtmlSignature("Tidio",             ["code.tidio.co"]),
    HtmlSignature("LiveChat",          ["cdn.livechatinc.com",
                                         "livechat-static.com"]),
    HtmlSignature("Olark",             ["static.olark.com"]),
    HtmlSignature("Chatwoot",          ["chatwoot.com/packs", "chatwoot.js"]),
    HtmlSignature("Salesforce Chat",   ["salesforceliveagent.com",
                                         "service.force.com/embeddedservice"]),
    HtmlSignature("Front Chat",        ["chat.frontapp.com"]),
    HtmlSignature("Pylon",             ["usepylon.com/pylon.js"]),
]


# ---------------------------------------------------------------------------
# Catalogue : Pixels publicitaires
# ---------------------------------------------------------------------------

_AD_PIXEL_SIGNATURES: list[HtmlSignature] = [
    HtmlSignature("Meta Pixel",             ["connect.facebook.net",
                                              "fbq('init'",
                                              'fbq("init"',
                                              "fbevents.js"]),
    HtmlSignature("LinkedIn Insight Tag",   ["snap.licdn.com",
                                              "linkedin.com/px",
                                              "_linkedin_partner_id"]),
    HtmlSignature("Google Ads",             ["googleadservices.com",
                                              "gtag('config', 'aw-",
                                              'gtag("config", "aw-']),
    HtmlSignature("Twitter/X Ads",          ["static.ads-twitter.com",
                                              "twq('init'",
                                              'twq("init"',
                                              "ads.twitter.com/uwt.js"]),
    HtmlSignature("TikTok Pixel",           ["analytics.tiktok.com",
                                              "ttq.load(",
                                              "tiktok-pixel"]),
    HtmlSignature("Reddit Ads",             ["rp.reddit.com",
                                              "redditads.js"]),
    HtmlSignature("Bing Ads",               ["bat.bing.com", "uetq"]),
    HtmlSignature("Pinterest Tag",          ["ct.pinterest.com",
                                              "pintrk("]),
    HtmlSignature("Snapchat Pixel",         ["tr.snapchat.com",
                                              "sc-static.net/scevent"]),
    HtmlSignature("Capterra Pixel",         ["ct.capterra.com"]),
    HtmlSignature("G2 Pixel",               ["tracking.g2.com"]),
    HtmlSignature("Demandbase",             ["tag.demandbase.com"]),
    HtmlSignature("Rollworks",              ["d.adroll.com",
                                              "rollworks.com"]),
]


# ---------------------------------------------------------------------------
# Catalogue : Analytics et outils de mesure
# Signal GTM : investissement en mesure = culture data = acheteur potentiel
# ---------------------------------------------------------------------------

_ANALYTICS_SIGNATURES: list[HtmlSignature] = [
    HtmlSignature("Google Analytics 4",         ["googletagmanager.com/gtag/js",
                                                  "gtag('config', 'g-",
                                                  'gtag("config", "g-']),
    HtmlSignature("Segment",                    ["cdn.segment.com",
                                                  "segment.io/analytics.js",
                                                  "analytics.load("]),
    HtmlSignature("Amplitude",                  ["cdn.amplitude.com",
                                                  "amplitude.com/libs",
                                                  "amplitude.init("]),
    HtmlSignature("Mixpanel",                   ["cdn.mxpnl.com",
                                                  "mixpanel.init(",
                                                  "mixpanel.com/lib"]),
    HtmlSignature("Hotjar",                     ["static.hotjar.com",
                                                  "hjid:", "_hjsettings"]),
    HtmlSignature("Plausible",                  ["plausible.io/js/plausible",
                                                  "plausible.io/js/script"]),
    HtmlSignature("PostHog",                    ["app.posthog.com",
                                                  "posthog.init(",
                                                  "cdn.posthog.com"]),
    HtmlSignature("Heap",                       ["heapanalytics.com",
                                                  "heap.load(",
                                                  "cdn.heapanalytics.com"]),
    HtmlSignature("FullStory",                  ["fullstory.com/s/fs.js",
                                                  "_fs_namespace"]),
    HtmlSignature("Microsoft Clarity",          ["clarity.ms/tag",
                                                  "clarity.ms/collect"]),
    HtmlSignature("Rudderstack",                ["cdn.rudderlabs.com",
                                                  "rudderstack.com"]),
]


# ---------------------------------------------------------------------------
# Patterns de detection des pages cles (URLs et texte HTML)
# ---------------------------------------------------------------------------

# Mots-cles dans le chemin des liens internes signalant une page pricing
_PRICING_URL_PATTERNS: list[str] = [
    "/pricing", "/tarif", "/plans", "/plan",
    "/price", "/prices", "/abonnement",
    "/subscription", "/upgrade",
]

# Mots-cles dans le chemin des liens internes signalant une page/formulaire demo
_DEMO_URL_PATTERNS: list[str] = [
    "/demo", "/request-demo", "/book-a-demo",
    "/schedule-demo", "/get-demo", "/try-demo",
    "/watch-demo", "/live-demo", "/demande-demo",
]

# Expressions dans le HTML (texte de boutons CTA, liens, etc.) signalant un flux demo
_DEMO_HTML_PATTERNS: list[str] = [
    "book a demo", "get a demo", "request a demo",
    "schedule a demo", "watch a demo", "try a demo",
    "book demo", "get demo", "request demo",
    "see a demo", "see it in action",
    "demander une demo", "reserver une demo",
    "schedule demo", "book your demo",
    "get started for free",    # souvent equivalent a un acces demo
    "start for free",
]

# Mots-cles dans le chemin des liens internes signalant une page recrutement
_CAREERS_URL_PATTERNS: list[str] = [
    "/careers", "/jobs", "/hiring",
    "/work-with-us", "/join-us",
    "/rejoindre", "/nous-rejoindre",
    "/offres-emploi", "/recrutement",
    "/open-positions", "/openings",
]


# ---------------------------------------------------------------------------
# Fonctions de detection internes
# ---------------------------------------------------------------------------


def _match_html(sig: HtmlSignature, html_lower: str) -> bool:
    """Retourne True si au moins un pattern est trouve dans le HTML (insensible a la casse)."""
    return any(p.lower() in html_lower for p in sig.patterns)


def _collect_matches(sigs: list[HtmlSignature], html_lower: str) -> list[str]:
    """Retourne la liste ordonnee et dedupliquee des noms detectes dans le HTML."""
    seen: set[str] = set()
    result: list[str] = []
    for sig in sigs:
        if sig.name not in seen and _match_html(sig, html_lower):
            seen.add(sig.name)
            result.append(sig.name)
    return result


def _links_contain_pattern(links: list[str], patterns: list[str]) -> bool:
    """
    Retourne True si au moins un lien interne contient au moins un pattern de chemin.

    La comparaison est insensible a la casse.
    """
    patterns_lower = [p.lower() for p in patterns]
    for link in links:
        link_lower = link.lower()
        if any(pat in link_lower for pat in patterns_lower):
            return True
    return False


def _html_contains_pattern(html_lower: str, patterns: list[str]) -> bool:
    """Retourne True si au moins un pattern est present dans le HTML."""
    return any(p.lower() in html_lower for p in patterns)


# ---------------------------------------------------------------------------
# Fonction principale publique
# ---------------------------------------------------------------------------


def detect_gtm_signals(data: ScrapedData) -> GtmSignals:
    """
    Detecte les signaux Go-To-Market dans le HTML et les liens internes de la page.

    Sources analysees :
    - data["html"]           : HTML brut pour les outils de tracking et le contenu CTA
    - data["internal_links"] : liens internes pour les pages cles (pricing, demo, careers)

    Interpretation des signaux pour une equipe sales :
    - chat_tools       : outils de contact client = proximite avec les utilisateurs
    - ad_pixels        : investissement en acquisition = budget marketing actif
    - analytics_tools  : culture data = equipe en croissance, acheteur potentiel
    - has_pricing_page : produit avec tarification affichee = SaaS monetise
    - has_demo_form    : intention commerciale explicite = funnel de vente actif
    - has_careers_page : recrutement actif = signal de croissance / Serie A+

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        GtmSignals: signaux identifies par categorie, sans doublons,
                    prets pour le scorer et le frontend.
    """
    # Securite defensive : les champs sont toujours presents mais peuvent etre vides
    html_lower: str = (data["html"] or "").lower()
    internal_links: list[str] = data["internal_links"] or []

    # Outils de chat / live support
    chat_tools = _collect_matches(_CHAT_SIGNATURES, html_lower)

    # Pixels publicitaires (investissement acquisition)
    ad_pixels = _collect_matches(_AD_PIXEL_SIGNATURES, html_lower)

    # Outils d'analytics avances (culture data)
    analytics_tools = _collect_matches(_ANALYTICS_SIGNATURES, html_lower)

    # Page pricing : signal d'un SaaS avec tarification accessible (fort signal B2B)
    has_pricing_page = _links_contain_pattern(internal_links, _PRICING_URL_PATTERNS)

    # Formulaire / page demo : double detection
    #   1. Lien interne vers une page dediee (/demo, /book-a-demo...)
    #   2. Texte CTA dans le HTML ("Book a Demo", "Get a Demo"...)
    has_demo_form = (
        _links_contain_pattern(internal_links, _DEMO_URL_PATTERNS)
        or _html_contains_pattern(html_lower, _DEMO_HTML_PATTERNS)
    )

    # Page careers : signal de recrutement actif = croissance en cours
    has_careers_page = _links_contain_pattern(internal_links, _CAREERS_URL_PATTERNS)

    return GtmSignals(
        chat_tools=chat_tools,
        ad_pixels=ad_pixels,
        analytics_tools=analytics_tools,
        has_pricing_page=has_pricing_page,
        has_demo_form=has_demo_form,
        has_careers_page=has_careers_page,
    )
