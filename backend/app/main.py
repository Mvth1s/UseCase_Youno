"""
Point d'entree de l'application FastAPI.
Configure le CORS, declare les routes et orchestre le pipeline d'analyse.

Pipeline : scraper -> tech_detector -> gtm_detector -> profiler -> scorer
Un seul appel LLM dans la chaine (profiler). Toutes les erreurs sont traduites
en codes HTTP explicites ; le frontend ne recoit jamais de 500 brut.
"""

from __future__ import annotations

import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.gtm_detector import detect_gtm_signals
from app.models import AnalyzeRequest, CompanyAnalysis
from app.profiler import build_profile
from app.scorer import compute_score
from app.scraper import scrape
from app.tech_detector import detect_tech_stack

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration CORS
# ---------------------------------------------------------------------------

_raw_origins: str = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: list[str] = (
    ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",")]
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Konsole Company Analyzer",
    description="Analyse un site web et renvoie le profil, la tech stack, les signaux GTM et un score B2B SaaS.",
    version="1.0.0",
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

    Orchestre en sequence : scraper -> tech_detector -> gtm_detector -> profiler -> scorer.
    Chaque exception metier est traduite en code HTTP approprie.

    Args:
        request: corps JSON contenant le champ "url".

    Returns:
        CompanyAnalysis: objet complet avec profil, tech stack, signaux GTM et score.

    Raises:
        HTTPException 400: URL invalide ou contenu non-HTML.
        HTTPException 503: site injoignable (DNS, timeout, statut non-2xx).
        HTTPException 500: erreur interne inattendue.
    """
    # --- Etape 1 : collecte ---
    try:
        scraped = scrape(request.url)
    except ValueError as exc:
        # URL invalide ou contenu non-HTML
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Le site n'a pas repondu dans le delai imparti : {request.url}",
        ) from exc
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de joindre le site : {request.url}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Le site a repondu avec une erreur HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.TooManyRedirects as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Trop de redirections pour atteindre : {request.url}",
        ) from exc
    except Exception as exc:
        logger.exception("Erreur inattendue lors du scraping de %s", request.url)
        raise HTTPException(status_code=500, detail="Erreur interne lors de la collecte.") from exc

    # --- Etapes 2 & 3 : detection (non-LLM, ne levent pas d'exception) ---
    tech_stack = detect_tech_stack(scraped)
    gtm_signals = detect_gtm_signals(scraped)

    # --- Etape 4 : profiler LLM (le fallback interne garantit qu'il ne leve jamais) ---
    profile = build_profile(scraped)

    # --- Etape 5 : scoring (pur calcul, ne leve pas d'exception) ---
    score = compute_score(profile, tech_stack, gtm_signals)

    return CompanyAnalysis(
        url=scraped["final_url"],
        page_title=scraped["page_title"],
        favicon_url=scraped["favicon_url"],
        tech_stack=tech_stack,
        gtm_signals=gtm_signals,
        profile=profile,
        score=score,
        error=None,
    )
