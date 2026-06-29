# CLAUDE.md — Règles du projet

## Contexte

Cas pratique technique pour **Youno** (plateforme SaaS *Konsole*, Revenue Engineering pour équipes sales/marketing).

**Mission :** une application web qui prend une URL de site (ex. `stripe.com`) et renvoie des informations exploitables sur l'entreprise : nom, description, tech stack détectée, secteur, taille approximative, signaux GTM. Bonus : un scoring "fit pour une boîte qui vend à des SaaS B2B".

**Contrainte de temps :** 5 à 8 heures. Un MVP qui tourne en production prime sur un projet ambitieux qui plante. Toujours arbitrer en faveur de la fiabilité.

## Stack imposée (ne pas dévier sans validation du CTO)

- **Frontend :** Vue 3 + Vite, déployé sur Netlify
- **Backend :** FastAPI (Python 3.11+), déployé sur Render (free tier)
- **LLM :** API Mistral (format compatible OpenAI), clé côté serveur uniquement
- **Scraping :** httpx + BeautifulSoup
- **Repo :** monorepo GitHub public, dossiers `backend/` et `frontend/` séparés

## Architecture cible

Pipeline séquentielle dans le backend, un seul endpoint `POST /analyze` qui orchestre :

1. **Collecte** (non-LLM) : fetch HTML via httpx, extraction title/meta/OG/favicon/liens/headers, gestion d'erreurs
2. **Détection tech stack** (non-LLM) : signatures dans HTML + headers
3. **Détection signaux GTM** (non-LLM) : chat (Intercom, Drift, Crisp), pixels (Meta, LinkedIn, Google Ads), analytics (GA4, Segment, Amplitude), page pricing, formulaire démo
4. **Profiler** (LLM Mistral) : nom, description, secteur, taille, audience B2B/B2C — sortie JSON forcée et parsée défensivement
5. **Scoring** (non-LLM) : logique de règles pondérées, explicable

Un seul appel LLM dans toute la chaîne (le Profiler) pour maîtriser coût, latence et risque de panne.

## Règles de code non négociables

- **Clés API jamais committées.** Toujours via variables d'environnement. Fournir un `.env.example`.
- **Découpage strict :** pas de logique métier dans les routes FastAPI. Chaque module a une responsabilité unique (`scraper.py`, `tech_detector.py`, `gtm_detector.py`, `profiler.py`, `scorer.py`).
- **Gestion d'erreurs explicite :** jamais de `except: pass`. Capturer les exceptions ciblées (timeout, statut HTTP, URL invalide, JSON LLM malformé), renvoyer des codes HTTP corrects et des messages exploitables côté frontend.
- **Typage :** annotations de type Python partout, modèles Pydantic pour les entrées/sorties de l'API.
- **CORS :** configuré explicitement pour autoriser le domaine Netlify en production.
- **Cold start Render :** le frontend doit gérer un premier appel lent (état loading clair, pas de timeout agressif).

## Conventions

- Français pour les commentaires et la documentation destinée à l'évaluation, anglais pour les noms de variables/fonctions.
- Pas de tirets cadratin ni de caractères invisibles dans les fichiers produits.
- Commits clairs et atomiques.

## Critères d'évaluation (à garder en tête en permanence)

L'évaluateur regarde : est-ce que ça tourne en live, qualité du code (structure, lisibilité, découpage, gestion d'erreurs), pertinence des choix techniques, sens produit (utilité réelle pour un utilisateur Konsole), le "try hard" (aller au bout), et la communication (README + Loom clairs).

## Rôles

Le pilotage humain est assuré par le CTO (Mathis). Les tâches sont suivies dans `TASKS.md`. Les subagents disponibles sont dans `.claude/agents/`. Voir leurs descriptions pour savoir quand déléguer.
