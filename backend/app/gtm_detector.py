"""
Module de detection des signaux Go-To-Market (GTM).
Implemente a l'etape 3 par l'agent detection-engineer.

Signaux recherches :
- Outils de chat client (Intercom, Drift, Crisp, HubSpot Chat...)
- Pixels publicitaires (Meta Pixel, LinkedIn Insight Tag, Google Ads...)
- Outils d'analytics avances (GA4, Segment, Amplitude, Mixpanel...)
- Presence d'une page pricing, d'un formulaire demo, d'une page careers
"""

from __future__ import annotations

from app.models import GtmSignals
from app.scraper import ScrapedData


def detect_gtm_signals(data: ScrapedData) -> GtmSignals:
    """
    Detecte les signaux GTM dans le HTML et les headers de la page.

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        GtmSignals: signaux identifies par categorie.

    Raises:
        NotImplementedError: jusqu'a l'etape 3.
    """
    raise NotImplementedError("gtm_detector.py sera implemente a l'etape 3 (agent detection-engineer).")
