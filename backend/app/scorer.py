"""
Module de scoring : calcul du score 'fit B2B SaaS' a partir de regles ponderees.
Implemente a l'etape 5 par l'agent scoring-engineer.

Logique : regles explicites et ponderees, robustes aux donnees manquantes.
Le score (0-100) est accompagne d'un label lisible et d'un breakdown par facteur.
"""

from __future__ import annotations

from app.models import CompanyProfile, GtmSignals, ScoreBreakdown, TechStack


def compute_score(
    profile: CompanyProfile,
    tech_stack: TechStack,
    gtm_signals: GtmSignals,
) -> ScoreBreakdown:
    """
    Calcule le score de fit B2B SaaS en appliquant des regles ponderees.

    Le score est deterministe, explicable et robuste : une donnee manquante
    vaut 0 point sans planter le calcul.

    Args:
        profile: profil entreprise produit par profiler.build_profile().
        tech_stack: technologies detectees par tech_detector.detect_tech_stack().
        gtm_signals: signaux GTM detectes par gtm_detector.detect_gtm_signals().

    Returns:
        ScoreBreakdown: score global, label et detail des facteurs.

    Raises:
        NotImplementedError: jusqu'a l'etape 5.
    """
    raise NotImplementedError("scorer.py sera implemente a l'etape 5 (agent scoring-engineer).")
