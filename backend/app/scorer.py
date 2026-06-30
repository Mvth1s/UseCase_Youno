"""
Module de scoring : calcul du score 'fit B2B SaaS' a partir de regles ponderees.

Ce module repond a la question :
  "Ce site est-il celui d'une entreprise cible pour un outil SaaS B2B
   vendu a des equipes sales/marketing ?"

Logique : regles explicites, ponderees et documentees -- aucun LLM.
Le score (0-100) est deterministe, clamp et accompagne d'un breakdown par facteur.

Pour ajuster les poids, modifier les constantes MAX_* et POINTS_* en debut de module.
Invariant a respecter : SUM(MAX_*) == 100 (verifie par assertion a l'import).

------------------------------------------------------------------------
Tableau des 8 facteurs (total max = 100 pts)
------------------------------------------------------------------------
 N  Facteur                               Source                  Max
 1  Audience B2B                          profile.audience         25
 2  Analytics avances (Segment, etc.)     gtm.analytics_tools      15
 3  Page pricing presente                 gtm.has_pricing_page     12
 4  Pixels publicitaires B2B              gtm.ad_pixels            12
 5  Formulaire demo / Contact sales       gtm.has_demo_form        10
 6  Outil de chat client                  gtm.chat_tools           10
 7  Taille entreprise (cible PME/ETI)     profile.estimated_size    8
 8  Stack tech moderne (Next.js, React)   tech_stack.frameworks     8
------------------------------------------------------------------------
"""

from __future__ import annotations

from app.models import CompanyProfile, GtmSignals, ScoreBreakdown, ScoreFactor, TechStack


# ---------------------------------------------------------------------------
# Poids par facteur
# Regle : ne jamais modifier MAX_* sans s'assurer que SUM(MAX_*) reste 100.
# ---------------------------------------------------------------------------

# --- Facteur 1 : Audience B2B (25 pts) ---
# Un outil B2B SaaS se vend en priorite a des entreprises elles-memes B2B.
# L'audience "mixed" est partiellement creditee : une cible hybride conserve
# une dimension B2B exploitable par une equipe sales.
MAX_AUDIENCE_B2B: int = 25
POINTS_AUDIENCE_B2B: int = 25   # audience == "B2B"
POINTS_AUDIENCE_MIXED: int = 12  # audience == "mixed" (B2B partiel)

# --- Facteur 2 : Analytics avances (15 pts) ---
# La presence d'outils comme Segment, Amplitude ou PostHog signale une culture
# data mature et une equipe produit/growth investie -- profil type d'acheteur SaaS.
# Progression par palier : plus l'investissement data est large, plus le signal est fort.
MAX_ADVANCED_ANALYTICS: int = 15
POINTS_ANALYTICS_ONE: int = 9        # 1 outil avance detecte
POINTS_ANALYTICS_TWO: int = 12       # 2 outils avances detectes
POINTS_ANALYTICS_THREE_PLUS: int = 15  # 3+ outils avances detectes
# Outils considered "avances" (excludes GA4 et Microsoft Clarity, trop generiques)
ADVANCED_ANALYTICS_TOOLS: frozenset[str] = frozenset({
    "Segment",
    "Amplitude",
    "Mixpanel",
    "Heap",
    "FullStory",
    "PostHog",
    "Rudderstack",
})

# --- Facteur 3 : Page pricing presente (12 pts) ---
# Un SaaS avec tarification publique a un cycle de vente structure et accessible.
# La page pricing indique que l'offre est formalisee : acheteur potentiel identifiable.
MAX_PRICING_PAGE: int = 12

# --- Facteur 4 : Pixels publicitaires B2B (12 pts) ---
# L'investissement en acquisition payante signale un budget marketing actif.
# LinkedIn est le signal le plus fort (audience de decideurs B2B).
# Google Ads et Bing complementent avec un poids moindre (audience plus large).
# Cumul des pixels detectes, plafonne a MAX_AD_PIXELS_B2B.
MAX_AD_PIXELS_B2B: int = 12
POINTS_PIXEL_LINKEDIN: int = 8    # LinkedIn Insight Tag : cible B2B professionnelle
POINTS_PIXEL_GOOGLE_ADS: int = 6  # Google Ads : large spectre, signal moyen
POINTS_PIXEL_BING: int = 3        # Bing Ads : signal complementaire, moins frequent
AD_PIXEL_LINKEDIN: str = "LinkedIn Insight Tag"
AD_PIXEL_GOOGLE_ADS: str = "Google Ads"
AD_PIXEL_BING: str = "Bing Ads"

# --- Facteur 5 : Formulaire demo / Contact sales (10 pts) ---
# Signal fort d'un cycle de vente B2B avec accompagnement humain.
# La presence d'une demo implique un processus commercial structure (AE ou BDR).
MAX_DEMO_FORM: int = 10

# --- Facteur 6 : Outil de chat client (10 pts) ---
# L'investissement dans un live chat (Intercom, Drift, Crisp...) revele une culture
# customer success developpee -- type d'equipe receptive aux outils d'aide a la vente.
MAX_CHAT_TOOL: int = 10

# --- Facteur 7 : Taille estimee de l'entreprise (8 pts) ---
# La PME 50-500 est la cible ideale : budget disponible, processus structures, agilite.
# Les startups ont le besoin mais pas toujours le budget.
# Les grandes entreprises ont des cycles de vente longs et des processus complexes.
MAX_COMPANY_SIZE: int = 8
POINTS_SIZE_PME: int = 8         # PME 50-500 : cible ideale
POINTS_SIZE_ETI: int = 6         # ETI 500-5000 : cycle plus long, budget reel
POINTS_SIZE_STARTUP: int = 4     # Startup <50 : early adopter possible, budget limite
POINTS_SIZE_ENTERPRISE: int = 2  # Grande entreprise >5000 : cycle complexe
# Valeurs exactes renvoyees par profiler.py (conformes au prompt systeme)
SIZE_PME: str = "PME 50-500"
SIZE_ETI: str = "ETI 500-5000"
SIZE_STARTUP: str = "startup <50"
SIZE_ENTERPRISE: str = "grande entreprise >5000"

# --- Facteur 8 : Stack tech moderne (8 pts) ---
# Une stack moderne (Next.js, React, Vue.js...) correle avec un budget tech eleve
# et une culture d'adoption d'outils. Signe indirect de maturite produit.
MAX_MODERN_TECH: int = 8
MODERN_FRAMEWORKS: frozenset[str] = frozenset({
    "Next.js",
    "Nuxt.js",
    "React",
    "Vue.js",
    "Angular",
    "Svelte",
    "SvelteKit",
    "Remix",
    "Gatsby",
})

# ---------------------------------------------------------------------------
# Verification statique : la somme des MAX doit etre exactement 100.
# Cette assertion echoue a l'import si quelqu'un modifie un MAX_* sans ajuster
# les autres -- protection contre les erreurs de calibration silencieuses.
# ---------------------------------------------------------------------------
_TOTAL_MAX: int = (
    MAX_AUDIENCE_B2B
    + MAX_ADVANCED_ANALYTICS
    + MAX_PRICING_PAGE
    + MAX_AD_PIXELS_B2B
    + MAX_DEMO_FORM
    + MAX_CHAT_TOOL
    + MAX_COMPANY_SIZE
    + MAX_MODERN_TECH
)
assert _TOTAL_MAX == 100, (
    f"Calibration invalide : SUM(MAX_*) = {_TOTAL_MAX} au lieu de 100. "
    "Ajuster les constantes MAX_* pour retrouver un total de 100."
)


# ---------------------------------------------------------------------------
# Labels qualitatifs selon le score final
# ---------------------------------------------------------------------------


def _score_label(score: int) -> str:
    """Retourne le label lisible correspondant au score normalise (0-100)."""
    if score >= 80:
        return "Cible ideale B2B SaaS"
    if score >= 60:
        return "Fort potentiel B2B"
    if score >= 40:
        return "Potentiel modere"
    if score >= 20:
        return "Faible signal B2B"
    return "Hors cible"


# ---------------------------------------------------------------------------
# Calcul de chaque facteur (fonctions privees, une par facteur)
# Chaque fonction retourne un ScoreFactor avec points et max renseignes.
# Si la donnee est absente ou vide, points = 0 (jamais d'exception).
# ---------------------------------------------------------------------------


def _factor_audience(profile: CompanyProfile) -> ScoreFactor:
    """
    Facteur 1 : Audience principale de l'entreprise.
    Valeurs attendues : 'B2B' (25 pts), 'mixed' (12 pts), 'B2C' ou vide (0 pt).
    """
    audience: str = (profile.audience or "").strip()
    if audience == "B2B":
        points = POINTS_AUDIENCE_B2B
    elif audience.lower() == "mixed":
        points = POINTS_AUDIENCE_MIXED
    else:
        # B2C explicite ou champ vide (profiler en echec) -> 0 pt
        points = 0
    return ScoreFactor(name="Audience B2B", points=points, max=MAX_AUDIENCE_B2B)


def _factor_advanced_analytics(gtm: GtmSignals) -> ScoreFactor:
    """
    Facteur 2 : Outils analytics avances (Segment, Amplitude, Mixpanel...).
    Progression par paliers : 1 outil = 9 pts, 2 = 12 pts, 3+ = 15 pts.
    GA4 et Microsoft Clarity exclus (trop generiques, peu differenciants).
    """
    advanced_count: int = sum(
        1 for tool in (gtm.analytics_tools or [])
        if tool in ADVANCED_ANALYTICS_TOOLS
    )
    if advanced_count == 0:
        points = 0
    elif advanced_count == 1:
        points = POINTS_ANALYTICS_ONE
    elif advanced_count == 2:
        points = POINTS_ANALYTICS_TWO
    else:
        points = POINTS_ANALYTICS_THREE_PLUS
    return ScoreFactor(
        name="Analytics avances (Segment, Amplitude, Mixpanel...)",
        points=points,
        max=MAX_ADVANCED_ANALYTICS,
    )


def _factor_pricing_page(gtm: GtmSignals) -> ScoreFactor:
    """
    Facteur 3 : Presence d'une page pricing.
    12 pts si detected, 0 sinon.
    """
    points: int = MAX_PRICING_PAGE if gtm.has_pricing_page else 0
    return ScoreFactor(name="Page pricing presente", points=points, max=MAX_PRICING_PAGE)


def _factor_ad_pixels_b2b(gtm: GtmSignals) -> ScoreFactor:
    """
    Facteur 4 : Pixels publicitaires B2B (LinkedIn, Google Ads, Bing).
    Accumulation : LinkedIn (8) + Google Ads (6) + Bing (3), plafonne a 12.
    """
    detected: set[str] = set(gtm.ad_pixels or [])
    raw_points: int = 0
    if AD_PIXEL_LINKEDIN in detected:
        raw_points += POINTS_PIXEL_LINKEDIN
    if AD_PIXEL_GOOGLE_ADS in detected:
        raw_points += POINTS_PIXEL_GOOGLE_ADS
    if AD_PIXEL_BING in detected:
        raw_points += POINTS_PIXEL_BING
    # Plafonnement explicite (LinkedIn + Google Ads = 14, reduit a 12)
    points: int = min(raw_points, MAX_AD_PIXELS_B2B)
    return ScoreFactor(
        name="Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)",
        points=points,
        max=MAX_AD_PIXELS_B2B,
    )


def _factor_demo_form(gtm: GtmSignals) -> ScoreFactor:
    """
    Facteur 5 : Presence d'un formulaire demo ou CTA 'Contact sales'.
    10 pts si detected, 0 sinon.
    """
    points: int = MAX_DEMO_FORM if gtm.has_demo_form else 0
    return ScoreFactor(
        name="Formulaire demo / Contact sales",
        points=points,
        max=MAX_DEMO_FORM,
    )


def _factor_chat_tool(gtm: GtmSignals) -> ScoreFactor:
    """
    Facteur 6 : Presence d'au moins un outil de chat client.
    10 pts des qu'un outil est detecte (Intercom, Drift, Crisp...), 0 sinon.
    """
    points: int = MAX_CHAT_TOOL if (gtm.chat_tools or []) else 0
    return ScoreFactor(
        name="Outil de chat client (Intercom, Drift, Crisp...)",
        points=points,
        max=MAX_CHAT_TOOL,
    )


def _factor_company_size(profile: CompanyProfile) -> ScoreFactor:
    """
    Facteur 7 : Taille estimee de l'entreprise.
    PME 50-500 = 8 pts (ideal), ETI = 6, startup = 4, grande entreprise = 2, vide = 0.
    """
    size: str = (profile.estimated_size or "").strip()
    if size == SIZE_PME:
        points = POINTS_SIZE_PME
    elif size == SIZE_ETI:
        points = POINTS_SIZE_ETI
    elif size == SIZE_STARTUP:
        points = POINTS_SIZE_STARTUP
    elif size == SIZE_ENTERPRISE:
        points = POINTS_SIZE_ENTERPRISE
    else:
        # Champ vide (profiler en echec ou taille non identifiee) -> 0 pt
        points = 0
    return ScoreFactor(
        name="Taille entreprise (cible PME/ETI)",
        points=points,
        max=MAX_COMPANY_SIZE,
    )


def _factor_modern_tech(tech_stack: TechStack) -> ScoreFactor:
    """
    Facteur 8 : Stack tech moderne (Next.js, React, Vue.js, Angular, Svelte...).
    8 pts si au moins un framework moderne est detecte, 0 sinon.
    """
    detected_frameworks: set[str] = set(tech_stack.frameworks or [])
    has_modern_stack: bool = bool(detected_frameworks & MODERN_FRAMEWORKS)
    points: int = MAX_MODERN_TECH if has_modern_stack else 0
    return ScoreFactor(
        name="Stack tech moderne (Next.js, React, Vue.js...)",
        points=points,
        max=MAX_MODERN_TECH,
    )


# ---------------------------------------------------------------------------
# Fonction principale publique
# ---------------------------------------------------------------------------


def compute_score(
    profile: CompanyProfile,
    tech_stack: TechStack,
    gtm_signals: GtmSignals,
) -> ScoreBreakdown:
    """
    Calcule le score de fit B2B SaaS en appliquant des regles ponderees.

    Le score est deterministe, explicable et robuste : une donnee manquante
    vaut 0 point sans planter le calcul. Le breakdown liste tous les facteurs,
    y compris ceux a 0 pt (transparence totale vers le frontend).

    Algorithme en 3 etapes :
      1. Evaluer chaque facteur independamment (8 fonctions isolees)
      2. Additionner les points bruts
      3. Clamper le resultat dans [0, 100] et choisir le label qualitatif

    Args:
        profile:     profil entreprise produit par profiler.build_profile().
        tech_stack:  technologies detectees par tech_detector.detect_tech_stack().
        gtm_signals: signaux GTM detectes par gtm_detector.detect_gtm_signals().

    Returns:
        ScoreBreakdown: score global (0-100), label qualitatif et detail des 8 facteurs.
    """
    # Evaluation independante de chaque facteur
    # L'ordre determine l'ordre d'affichage dans le breakdown (du plus au moins pondere)
    factors: list[ScoreFactor] = [
        _factor_audience(profile),
        _factor_advanced_analytics(gtm_signals),
        _factor_pricing_page(gtm_signals),
        _factor_ad_pixels_b2b(gtm_signals),
        _factor_demo_form(gtm_signals),
        _factor_chat_tool(gtm_signals),
        _factor_company_size(profile),
        _factor_modern_tech(tech_stack),
    ]

    # Somme des contributions individuelles
    raw_score: int = sum(f.points for f in factors)

    # Plafonnement defensif : par construction MAX = 100, mais on protege quand meme
    score: int = max(0, min(100, raw_score))

    return ScoreBreakdown(
        score=score,
        label=_score_label(score),
        factors=factors,
    )
