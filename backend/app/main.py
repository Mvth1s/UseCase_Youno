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
import time

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
# Cache memoire TTL 1h
# Adapte au free tier Render (meme process, pas de Redis).
# Limite connue : cache perdu au redemarrage du worker.
# ---------------------------------------------------------------------------

# Duree de validite d'une entree (en secondes)
CACHE_TTL_SECONDS: int = 3600

# Plafond d'entrees pour eviter une fuite memoire sur le free tier
CACHE_MAX_ENTRIES: int = 200

# Structure : url_normalisee -> (monotonic_timestamp, CompanyAnalysis)
_analysis_cache: dict[str, tuple[float, "CompanyAnalysis"]] = {}


def _cache_key(url: str) -> str:
    """Normalise l'URL en cle de cache stable (casse et slash finaux ignores)."""
    return url.strip().lower().rstrip("/")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
@app.head("/health")
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
    # --- Cache : court-circuit si resultat frais disponible (< 1h) ---
    cache_key = _cache_key(request.url)
    cached = _analysis_cache.get(cache_key)
    if cached is not None:
        ts, cached_result = cached
        if time.monotonic() - ts < CACHE_TTL_SECONDS:
            logger.info("[cache] Hit pour %s", cache_key)
            return cached_result
        # Entree expiree : nettoyage immediat
        del _analysis_cache[cache_key]

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

    result = CompanyAnalysis(
        url=scraped["final_url"],
        page_title=scraped["page_title"],
        favicon_url=scraped["favicon_url"],
        tech_stack=tech_stack,
        gtm_signals=gtm_signals,
        profile=profile,
        score=score,
        error=None,
    )

    # --- Mise en cache avec eviction de l'entree la plus ancienne si plafond atteint ---
    if len(_analysis_cache) >= CACHE_MAX_ENTRIES:
        oldest = min(_analysis_cache, key=lambda k: _analysis_cache[k][0])
        del _analysis_cache[oldest]
    _analysis_cache[cache_key] = (time.monotonic(), result)

    return result
