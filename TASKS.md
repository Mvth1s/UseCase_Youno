# TASKS.md — Pilotage du projet

Fichier de suivi maintenu par le CTO (Mathis). Chaque tâche a une définition de "terminé". On avance en séquence : un dev implémente, le `code-reviewer` passe, le CTO valide, puis tâche suivante. La doc clôt le tout.

Statuts : `TODO` / `EN COURS` / `EN REVIEW` / `VALIDÉ`

---

## Étape 0 — Cadrage (CTO)

- [ ] Repo GitHub public créé, monorepo `backend/` + `frontend/`
- [ ] Clé API Mistral obtenue, comptes Render et Netlify prêts
- [ ] CLAUDE.md et subagents en place

**Terminé quand :** le repo existe et les accès sont prêts.

---

## Étape 1 — Architecture — agent `architect` — `TODO`

- [ ] Arborescence monorepo, `.gitignore`, `.env.example`
- [ ] Squelette FastAPI avec `POST /analyze` renvoyant un mock complet, modèles Pydantic, CORS
- [ ] Squelette Vue + Vite appelant le backend et affichant le résultat
- [ ] Contrat d'API (schéma JSON entrée/sortie) documenté

**Terminé quand :** le frontend appelle le backend et affiche le mock, de bout en bout, en local.

---

## Étape 2 — Collecte — agent `backend-scraper` — `TODO`

- [ ] `scraper.py` : normalisation d'URL, fetch httpx, extraction BeautifulSoup
- [ ] Gestion d'erreurs complète (timeout, DNS, non-200, non-HTML, URL invalide)
- [ ] Testé sur 4-5 URLs réelles variées, comportement documenté

**Terminé quand :** le scraper renvoie une donnée structurée fiable et ne fait jamais planter l'API.
**Review puis validation CTO.**

---

## Étape 3 — Détection — agent `detection-engineer` — `TODO`

- [ ] `tech_detector.py` : frameworks, headers, CDN, CMS, avec preuve par signature
- [ ] `gtm_detector.py` : chat, pixels, analytics, pricing, démo, careers, par catégorie
- [ ] Sortie structurée et extensible

**Terminé quand :** les deux modules détectent correctement les signaux sur les URLs de test. Soigner le GTM (différenciateur).
**Review puis validation CTO.**

---

## Étape 4 — Profiler LLM — agent `llm-integrator` — `TODO`

- [ ] `profiler.py` : appel Mistral, JSON forcé, parsing défensif, fallback
- [ ] Clé via variable d'environnement
- [ ] Échec du LLM ne bloque pas le reste de l'analyse (profil partiel signalé)

**Terminé quand :** le Profiler renvoie un JSON structuré fiable et dégrade proprement en cas d'échec.
**Review puis validation CTO.**

---

## Étape 5 — Scoring (bonus) — agent `scoring-engineer` — `TODO`

- [ ] `scorer.py` : règles pondérées, poids nommés et documentés
- [ ] Sortie avec score, label et breakdown explicable
- [ ] Robuste aux données manquantes

**Terminé quand :** le score est calculé, explicable oralement, et le breakdown s'affiche.
**Review puis validation CTO.**

---

## Étape 6 — Intégration backend

- [ ] L'endpoint `/analyze` orchestre la pipeline complète (collecte > détection > profiler > scoring)
- [ ] Réponse finale conforme au contrat d'API
- [ ] Testé bout en bout en local sur plusieurs URLs

**Terminé quand :** une vraie URL en entrée produit une analyse complète réelle.
**Review puis validation CTO.**

---

## Étape 7 — Frontend — agent `frontend-vue` — `TODO`

- [ ] UI sections : identité, tech stack, signaux GTM (mis en valeur), score
- [ ] État loading gérant le cold start, messages d'erreur clairs
- [ ] Composants découpés

**Terminé quand :** l'UI affiche proprement une analyse réelle et gère les erreurs.
**Review puis validation CTO.**

---

## Étape 8 — Déploiement — agent `devops-deploy` — `TODO`

- [ ] Backend déployé sur Render, frontend sur Netlify
- [ ] Variables d'environnement en prod, CORS prod vérifié réellement
- [ ] Uptime monitoring contre le cold start
- [ ] Flux complet testé sur le lien live

**Terminé quand :** l'app fonctionne via le lien public, testée sur plusieurs URLs réelles.
**Critère le plus lourd du test.**

---

## Étape 9 — Documentation — agent `documentation-writer` — `TODO`

- [ ] README complet (choix techniques, archi, lancement local, sens produit, limites)
- [ ] Docstrings backend
- [ ] Trame du Loom (5-8 min)

**Terminé quand :** un évaluateur peut tout comprendre et lancer le projet à partir du README.

---

## Étape 10 — Livraison (CTO)

- [ ] Loom principal (5-8 min) : démo, archi, pitch d'intégration Konsole
- [ ] Loom bonus (3-5 min) : présentation d'un side project
- [ ] Formulaire Airtable rempli + mail à christian.lim@youno.fr

**Terminé quand :** tout est soumis dans les délais (1 semaine).

---

## Notes de pilotage

- Priorité absolue : un MVP qui tourne en live. En cas de manque de temps, le scoring (étape 5) est le premier sacrifiable, le déploiement (étape 8) ne l'est jamais.
- Le contexte ne passe pas tout seul d'un agent à l'autre : c'est le CTO qui transporte les décisions et les sorties entre les sessions.
