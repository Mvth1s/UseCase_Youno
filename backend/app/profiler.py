"""
Module de profilage LLM : appel unique a l'API Mistral pour inferer le profil de l'entreprise.
Implemente a l'etape 4 par l'agent llm-integrator.

Contraintes :
- Un seul appel LLM dans toute la chaine.
- Sortie JSON forcee et parsee defensivement.
- En cas d'echec du LLM, renvoyer un CompanyProfile partiel (champs vides) sans lever d'exception.
"""

from __future__ import annotations

from app.models import CompanyProfile
from app.scraper import ScrapedData


def build_profile(data: ScrapedData) -> CompanyProfile:
    """
    Appelle l'API Mistral avec le contenu scrape pour produire le profil entreprise.

    Le prompt force une sortie JSON stricte contenant : name, description,
    sector, estimated_size, audience. Le parsing est defensif : tout champ
    manquant ou mal forme est remplace par une chaine vide.

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        CompanyProfile: profil infere, potentiellement partiel si le LLM echoue.

    Raises:
        NotImplementedError: jusqu'a l'etape 4.
    """
    raise NotImplementedError("profiler.py sera implemente a l'etape 4 (agent llm-integrator).")
