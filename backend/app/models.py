"""
Modeles Pydantic definissant le contrat d'entree/sortie de l'API.
Tout changement de schema doit etre repercute dans API_CONTRACT.md.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Entree
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """Corps de la requete POST /analyze."""

    url: str

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        """Ajoute le schema https:// si absent, pour simplifier la validation aval."""
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            value = "https://" + value
        return value


# ---------------------------------------------------------------------------
# Sous-objets de la reponse
# ---------------------------------------------------------------------------


class TechStack(BaseModel):
    """Technologies detectees dans le HTML et les headers HTTP."""

    frameworks: list[str] = []
    cdn: list[str] = []
    cms: list[str] = []
    server: list[str] = []
    analytics: list[str] = []
    tag_managers: list[str] = []
    other: list[str] = []


class GtmSignals(BaseModel):
    """Signaux Go-To-Market detectes sur le site (outils, pixels, pages cles)."""

    chat_tools: list[str] = []
    ad_pixels: list[str] = []
    analytics_tools: list[str] = []
    has_pricing_page: bool = False
    has_demo_form: bool = False
    has_careers_page: bool = False


class CompanyProfile(BaseModel):
    """Profil de l'entreprise infere par le LLM Mistral a partir du contenu scrape."""

    name: str = ""
    description: str = ""
    sector: str = ""
    estimated_size: str = ""
    audience: str = ""  # valeurs attendues : "B2B", "B2C", "mixed"


class ScoreFactor(BaseModel):
    """Detail d'un facteur individuel du scoring B2B SaaS."""

    name: str
    points: int
    max: int


class ScoreBreakdown(BaseModel):
    """Score global et detail des facteurs pour le 'fit B2B SaaS'."""

    score: int  # 0-100
    label: str  # ex. "Fort potentiel B2B SaaS"
    factors: list[ScoreFactor] = []


# ---------------------------------------------------------------------------
# Reponse agregee
# ---------------------------------------------------------------------------


class CompanyAnalysis(BaseModel):
    """Reponse complete de l'endpoint POST /analyze."""

    url: str
    page_title: str = ""
    favicon_url: Optional[str] = None
    tech_stack: TechStack = TechStack()
    gtm_signals: GtmSignals = GtmSignals()
    profile: CompanyProfile = CompanyProfile()
    score: ScoreBreakdown = ScoreBreakdown(score=0, label="", factors=[])
    error: Optional[str] = None
