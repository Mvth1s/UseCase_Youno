"""
Module de collecte : normalisation d'URL, fetch HTTP et extraction du contenu HTML.
Implemente a l'etape 2 par l'agent backend-scraper.
"""

from __future__ import annotations

from typing import TypedDict


class ScrapedData(TypedDict):
    """Donnees brutes extraites d'une page web."""

    url: str
    final_url: str
    status_code: int
    html: str
    page_title: str
    meta_description: str
    favicon_url: str | None
    response_headers: dict[str, str]


def scrape(url: str) -> ScrapedData:
    """
    Normalise l'URL, effectue le fetch HTTP et extrait les metadonnees de base.

    Args:
        url: URL du site a analyser (schema inclus).

    Returns:
        ScrapedData: donnees brutes prates pour les modules de detection.

    Raises:
        NotImplementedError: jusqu'a l'etape 2.
        httpx.TimeoutException: si le site ne repond pas dans le delai imparti.
        ValueError: si l'URL est invalide ou le contenu n'est pas du HTML.
    """
    raise NotImplementedError("scraper.py sera implemente a l'etape 2 (agent backend-scraper).")
