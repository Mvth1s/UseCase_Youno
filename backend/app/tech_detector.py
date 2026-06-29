"""
Module de detection de la tech stack a partir du HTML et des headers HTTP.
Implemente a l'etape 3 par l'agent detection-engineer.
"""

from __future__ import annotations

from app.models import TechStack
from app.scraper import ScrapedData


def detect_tech_stack(data: ScrapedData) -> TechStack:
    """
    Analyse le HTML et les headers HTTP pour identifier les technologies utilisees.

    Strategies de detection : signatures dans le HTML (scripts, classes CSS, attributs),
    headers HTTP (Server, X-Powered-By, etc.), et meta tags.

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        TechStack: technologies identifiees par categorie, avec preuve par signature.

    Raises:
        NotImplementedError: jusqu'a l'etape 3.
    """
    raise NotImplementedError("tech_detector.py sera implemente a l'etape 3 (agent detection-engineer).")
