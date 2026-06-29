"""
Point d'entree de l'application FastAPI.
Configure le CORS, declare les routes et orchestre le pipeline d'analyse.

A ce stade (etape 1), l'endpoint /analyze renvoie un mock complet pour
valider l'integration frontend <-> backend sans logique metier reelle.
Les modules metier seront actives au fur et a mesure des etapes suivantes.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AnalyzeRequest,
    CompanyAnalysis,
    CompanyProfile,
    GtmSignals,
    ScoreBreakdown,
    ScoreFactor,
    TechStack,
)

# Imports metier (commentes jusqu'a implementation de chaque etape)
# from app.scraper import scrape
# from app.tech_detector import detect_tech_stack
# from app.gtm_detector import detect_gtm_signals
# from app.profiler import build_profile
# from app.scorer import compute_score

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration CORS
# ---------------------------------------------------------------------------

_raw_origins: str = os.getenv("ALLOWED_ORIGINS", "*")
# Supporte une liste separee par des virgules ou le wildcard "*"
ALLOWED_ORIGINS: list[str] = (
    ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",")]
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Konsole Company Analyzer",
    description="Analyse un site web et renvoie le profil, la tech stack, les signaux GTM et un score B2B SaaS.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint de sante utilise par Render pour les healthchecks."""
    return {"status": "ok"}


@app.post("/analyze", response_model=CompanyAnalysis)
def analyze(request: AnalyzeRequest) -> CompanyAnalysis:
    """
    Pipeline principale d'analyse d'un site web.

    Etape actuelle : renvoie un mock realiste base sur stripe.com.
    Les etapes suivantes remplaceront chaque bloc par la vraie implementation.

    Args:
        request: corps JSON contenant le champ "url".

    Returns:
        CompanyAnalysis: objet complet avec profil, tech stack, signaux GTM et score.

    Raises:
        HTTPException 400: URL manquante ou manifestement invalide.
        HTTPException 503: site injoignable (active apres implementation du scraper).
        HTTPException 500: erreur interne inattendue.
    """

    if not request.url:
        raise HTTPException(status_code=400, detail="Le champ 'url' est obligatoire.")

    # ------------------------------------------------------------------
    # MOCK — donnees factices realistes pour stripe.com
    # Remplacer ce bloc par les vraies etapes quand elles seront prates.
    # ------------------------------------------------------------------

    mock_result = CompanyAnalysis(
        url=request.url,
        page_title="Stripe | Financial Infrastructure to Grow Your Revenue",
        favicon_url="https://stripe.com/favicon.ico",
        tech_stack=TechStack(
            frameworks=["React", "Next.js"],
            cdn=["Cloudflare"],
            cms=[],
            server=["nginx"],
            analytics=["Google Analytics 4", "Segment"],
            tag_managers=["Google Tag Manager"],
            other=["Stripe.js", "reCAPTCHA"],
        ),
        gtm_signals=GtmSignals(
            chat_tools=["Intercom"],
            ad_pixels=["LinkedIn Insight Tag", "Meta Pixel", "Google Ads"],
            analytics_tools=["Google Analytics 4", "Segment", "Amplitude"],
            has_pricing_page=True,
            has_demo_form=False,
            has_careers_page=True,
        ),
        profile=CompanyProfile(
            name="Stripe",
            description=(
                "Stripe est une infrastructure financiere en ligne qui permet aux "
                "entreprises d'accepter des paiements, d'envoyer des versements et "
                "de gerer leurs revenus a l'echelle mondiale."
            ),
            sector="Fintech / Paiements",
            estimated_size="5000-10000 employes",
            audience="B2B",
        ),
        score=ScoreBreakdown(
            score=87,
            label="Fort potentiel B2B SaaS",
            factors=[
                ScoreFactor(name="Audience B2B confirmee", points=25, max=25),
                ScoreFactor(name="Signaux analytics avances (Segment, Amplitude)", points=20, max=20),
                ScoreFactor(name="Page pricing presente", points=15, max=15),
                ScoreFactor(name="Pixels publicitaires B2B (LinkedIn)", points=15, max=15),
                ScoreFactor(name="Chat client (Intercom)", points=12, max=15),
                ScoreFactor(name="Formulaire demo absent", points=0, max=10),
            ],
        ),
        error=None,
    )

    return mock_result
