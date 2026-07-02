# Konsole Company Analyzer

**Application live :** https://usecaseyouno.netlify.app | **Backend :** https://usecase-youno.onrender.com | **Repo :** https://github.com/Mvth1s/UseCase_Youno

Outil d'analyse de sites web qui prend une URL (ex. `stripe.com`) et renvoie en quelques secondes le profil de l'entreprise, sa tech stack, ses signaux Go-To-Market et un score de fit "B2B SaaS" -- concu comme une brique de qualification de prospects pour Konsole, la plateforme Revenue Engineering de Youno.

---

## Sens produit

Pour un commercial sur Konsole, qualifier un prospect commence par repondre a trois questions : qu'est-ce que cette entreprise fait, comment est-elle organisee, et investit-elle deja dans des outils marketing et sales ?

Cet outil repond automatiquement a ces questions a partir de l'URL du site :

- **Tech stack** : une entreprise sur Next.js + Cloudflare + Stripe a une equipe technique mature et un produit en production. C'est un signal de maturite produit, donc de capacite a adopter un outil SaaS supplementaire.
- **Signaux GTM** : la presence d'un LinkedIn Insight Tag indique que l'entreprise achete de la publicite B2B. Un Intercom ou un Drift indique un investissement dans l'engagement client. Une page `/pricing` publique indique un SaaS avec un cycle de vente accessible et une tarification formalisee.
- **Score B2B SaaS (0-100)** : synthese ponderee de ces signaux en un seul chiffre actionnable, accompagne d'un label qualitatif ("Cible ideale B2B SaaS", "Fort potentiel B2B", etc.) et du detail de chaque facteur. Un commercial peut lire le score en trois secondes et comprendre pourquoi en dix.

Cote interface, les 10 dernieres analyses sont conservees en localStorage et restituees instantanement depuis le panneau historique, sans re-appel au backend. La latence de chaque analyse est affichee, et le JSON complet est exportable en un clic pour alimenter un autre outil ou un webhook Konsole.

---

## Architecture

### Pipeline sequentielle

```
URL saisie
    |
    v
[scraper.py]          Fetch HTTP (httpx), extraction BeautifulSoup
    |                 Sortie : HTML, title, meta, OG, liens, texte visible
    |
    v
[tech_detector.py]    Signatures dans le HTML et les headers HTTP
    |                 Sortie : frameworks, CDN, CMS, serveur, analytics, tag managers
    |
    v
[gtm_detector.py]     Signatures GTM dans le HTML et les liens internes
    |                 Sortie : chat, pixels, analytics, pricing, demo, careers
    |
    v
[profiler.py]         Seul appel LLM (Mistral) -- JSON force, parsing defensif
    |                 Sortie : nom, description, secteur, taille, audience
    |
    v
[scorer.py]           Regles ponderees, aucun LLM
    |                 Sortie : score 0-100, label, breakdown des 8 facteurs
    |
    v
CompanyAnalysis       Reponse JSON complete renvoyee par POST /analyze
```

Chaque etape produit un objet structure consomme par l'etape suivante. Seul `main.py` orchestre la pipeline -- aucun module metier n'en importe un autre.

### Modules

| Fichier | Responsabilite |
|---|---|
| `app/main.py` | Route `POST /analyze`, CORS, orchestration pipeline, cache memoire TTL 1h (max 200 entrees, eviction LRU), rate limiting 10 req/min par IP via slowapi |
| `app/scraper.py` | Normalisation URL, fetch httpx avec gestion manuelle des redirections, extraction BeautifulSoup, protection SSRF |
| `app/tech_detector.py` | Detection tech stack par signatures HTML et headers HTTP |
| `app/gtm_detector.py` | Detection signaux GTM (outils de chat, pixels publicitaires, analytics, pages cles) |
| `app/profiler.py` | Appel API Mistral, sortie JSON forcee, parsing defensif en trois passes, normalisation `estimated_size`, fallback sur metadonnees |
| `app/scorer.py` | Calcul du score "fit B2B SaaS" par regles ponderees, breakdown des 8 facteurs |
| `app/models.py` | Modeles Pydantic pour la validation des entrees et la serialisation des sorties |

---

## Choix techniques

**Vue 3 + Vite** -- Framework front maîtrise, configuration zero-friction, build optimise en quelques secondes. L'application n'expose qu'un seul ecran utile (analyser une URL) decline en quatre etats (idle, loading, resultat, erreur) geres par un simple `ref` dans `App.vue`, sans navigation entre routes ni besoin de deep-linking : Vue Router ou Nuxt resteraient une surcouche injustifiee. La complexite reelle est absorbee par la composition de composants (`ResultView` decoupe en `ProfileCard`, `ScoreCard`, `GtmCard`, `TechStackCard`), pas par du routage. Vite 8 propose un build tres rapide avec des bundles optimises sans configuration supplementaire.

**FastAPI** -- Typage natif via Pydantic, documentation Swagger generee automatiquement, validation stricte des entrees/sorties. Idéal pour un endpoint unique avec un contrat d'API formalise. La gestion des erreurs explicite (HTTP 400/503 selon la cause) est triviale a implementer avec les `HTTPException` FastAPI.

**Mistral AI** -- Un seul appel LLM dans toute la chaine (le module `profiler.py`). Ce choix est delibere : il limite le cout (une requete Mistral par analyse), la latence (pas de chaine d'agents), et le risque de panne (les etapes de detection sont 100 % non-LLM et toujours disponibles). `mistral-small-latest` offre un bon ratio qualite/cout/latence pour une tache de qualification structuree avec JSON force (le modele est contraint a repondre selon un schema JSON strict et valide automatiquement, plutot qu'en texte libre a parser a la main).

**httpx + BeautifulSoup** -- httpx permet le controle fin des redirections, necessaire pour la protection anti-SSRF (Server-Side Request Forgery : sans verification, une URL malveillante pourrait forcer le serveur a interroger des ressources internes comme le reseau cloud ou `localhost` ; chaque saut de redirection est donc revalide). Le streaming du body limite la consommation memoire sur les pages volumineuses. BeautifulSoup avec le parseur `html.parser` est robuste sans dependance systeme. Playwright ou Selenium n'ont pas ete retenus : le rendu JavaScript ajoute plusieurs secondes de latence et complexifie considerablement le deploiement, pour un gain marginal sur la majorite des sites.

**Detection par signatures (non-LLM)** -- Toute la detection tech stack et GTM repose sur des correspondances de patterns dans le HTML brut et les headers HTTP. Ce choix garantit la transparence (chaque resultat est la preuve directe d'une signature presente dans la source), la vitesse (pas d'appel reseau supplementaire), et l'extensibilite (ajouter un outil = ajouter une ligne dans la liste correspondante, sans modifier la logique de detection).

**Cache memoire TTL 1h** (time-to-live : duree de vie d'une entree avant expiration automatique) -- Un dictionnaire en memoire dans le worker Uvicorn evite de re-scraper et de re-appeler Mistral pour la meme URL dans la meme heure. C'est volontairement simple : pas de Redis (surcouche injustifiee pour un MVP), pas de persistance entre redemarrages du worker (documentee comme limite connue). L'eviction LRU (Least Recently Used : l'entree la moins recemment consultee est supprimee en premier) sur un plafond de 200 entrees previent les fuites memoire sur le free tier.

**Rate limiting (slowapi, 10 req/min par IP)** -- Un seul appel LLM coute entre 0,001 et 0,01 dollar. Sans protection, un bot peut vider le credit Mistral en quelques minutes. slowapi s'integre en deux lignes au-dessus de la route sans modifier la logique metier ; la reponse 429 est standard et geree explicitement par le frontend.

**Netlify + Render** -- Netlify pour le frontend : deploiement automatique depuis Git, CDN mondial, TLS et redirections SPA configures par `netlify.toml`. Render pour le backend : deploiement depuis `render.yaml` (Blueprint, le format de configuration declarative de Render qui evite de ressaisir les parametres manuellement dans l'interface), restart automatique, plan gratuit suffisant pour un MVP.

---

## Lancement en local

### Prerequis

- Python 3.11 ou superieur
- Node.js 20 ou superieur
- Une cle API Mistral (https://console.mistral.ai)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis renseigner MISTRAL_API_KEY dans .env
uvicorn app.main:app --reload  # http://localhost:8000
```

Verification :

```bash
curl http://localhost:8000/health
# {"status":"ok"}

# HEAD est egalement supporte (utilise par UptimeRobot)
curl -I http://localhost:8000/health

curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "stripe.com"}'
```

Extrait de la reponse (schema complet et description de chaque champ dans `backend/API_CONTRACT.md`) :

```json
{
  "url": "https://stripe.com",
  "page_title": "Stripe | Financial Infrastructure to Grow Your Revenue",
  "tech_stack": { "frameworks": ["React", "Next.js"], "cdn": ["Cloudflare"] },
  "gtm_signals": { "chat_tools": ["Intercom"], "has_pricing_page": true },
  "profile": { "name": "Stripe", "sector": "Fintech / Paiements", "audience": "B2B" },
  "score": { "score": 87, "label": "Cible ideale B2B SaaS" }
}
```

Tests unitaires (105 tests sur les trois modules deterministes) :

```bash
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # VITE_API_URL=http://localhost:8000
npm run dev                    # http://localhost:5173
```

---

## Variables d'environnement

| Variable | Fichier | Usage |
|---|---|---|
| `MISTRAL_API_KEY` | `backend/.env` | Cle d'authentification pour l'API Mistral |
| `ALLOWED_ORIGINS` | `backend/.env` | Origines CORS autorisees (URL Netlify en production, `*` en developpement local) |
| `VITE_API_URL` | `frontend/.env.local` | URL du backend appelee par Vue |

Les fichiers `.env.example` dans chaque dossier contiennent les valeurs par defaut pour le developpement local.

---

## Integration continue

Deux workflows GitHub Actions declenchent automatiquement sur `push` et `pull_request` vers `main` et `dev`.

**Backend** (`.github/workflows/backend.yml`) : verification syntaxique (`py_compile`), validation des imports avec une cle factice, puis execution des 105 tests unitaires via `pytest tests/ -v`. Le workflow ne passe que sur les chemins `backend/**`.

**Frontend** (`.github/workflows/frontend.yml`) : `npm ci` + `npm run build` avec l'URL backend de production injectee en variable d'environnement. Verifie que `dist/index.html` est present a l'issue du build. Le workflow ne passe que sur les chemins `frontend/**`.

---

## Deploiement

### Ordre obligatoire

1. Deployer le backend sur Render (obtenir l'URL generee)
2. Deployer le frontend sur Netlify (injecter l'URL Render dans `VITE_API_URL`)
3. Revenir sur Render pour renseigner `ALLOWED_ORIGINS` avec l'URL Netlify

### Backend (Render)

1. render.com -> **New** -> **Web Service** -> connecter le repo GitHub `Mvth1s/UseCase_Youno`
2. Render detecte `backend/render.yaml` automatiquement (Blueprint). Si ce n'est pas le cas, renseigner manuellement :
   - **Root directory** : `backend`
   - **Build command** : `pip install -r requirements.txt`
   - **Start command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path** : `/health`
3. Dans l'onglet **Environment**, ajouter les variables :
   - `MISTRAL_API_KEY` : la cle API Mistral
   - `ALLOWED_ORIGINS` : laisser vide pour l'instant (a remplir apres le deploiement Netlify)
   - `PYTHON_VERSION` : `3.11.0`
4. Cliquer **Deploy**. Copier l'URL generee (ex. `https://usecase-youno.onrender.com`).

### Frontend (Netlify)

1. netlify.com -> **Add new site** -> **Import from Git** -> connecter le repo GitHub
2. Netlify detecte `frontend/netlify.toml`. Verifier les parametres :
   - **Base directory** : `frontend`
   - **Build command** : `npm run build`
   - **Publish directory** : `frontend/dist`
3. Dans **Site configuration** -> **Environment variables**, ajouter :
   - `VITE_API_URL` : l'URL Render copiee a l'etape precedente
4. Cliquer **Deploy site**. Copier l'URL generee (ex. `https://usecaseyouno.netlify.app`).

### Finalisation CORS

1. Retourner sur Render -> onglet **Environment** du service backend
2. Mettre a jour `ALLOWED_ORIGINS` avec l'URL Netlify exacte
3. Cliquer **Save changes** -> Render redeploit automatiquement

### Cold start Render (free tier)

Render endort les services gratuits apres 15 minutes d'inactivite. Le premier appel apres une periode de sommeil prend 30 a 60 secondes. Le frontend affiche un etat de chargement explicite et un timeout de 60 secondes pour absorber ce delai cote utilisateur.

En usage normal, un moniteur UptimeRobot ping `/health` toutes les 5 minutes, ce qui maintient le backend eveille en continu : le delai de 30 a 60 secondes ne se produit que si ce moniteur est desactive ou indisponible.

Pour maintenir le backend eveille, un script de warm-up est inclus :

```bash
python backend/warmup.py https://usecase-youno.onrender.com
```

Ce script ping `/health` toutes les 14 minutes. Il peut tourner localement ou etre configure comme cron gratuit sur cron-job.org ou UptimeRobot.

---

## Structure du repo

```
UseCase_Youno/
|
+-- backend/                  FastAPI (Python 3.11)
|   +-- app/
|   |   +-- main.py           Route POST /analyze, CORS, orchestration pipeline, cache TTL, rate limiting
|   |   +-- scraper.py        Fetch httpx + extraction BeautifulSoup + protection SSRF
|   |   +-- tech_detector.py  Detection stack par signatures HTML et headers
|   |   +-- gtm_detector.py   Detection signaux GTM (chat, pixels, analytics, pages cles)
|   |   +-- profiler.py       Appel Mistral, JSON force, parsing defensif, normalisation taille, fallback
|   |   +-- scorer.py         Score pondere "fit B2B SaaS", breakdown explicable
|   |   +-- models.py         Modeles Pydantic entree/sortie
|   +-- tests/
|   |   +-- test_scorer.py         Tests unitaires scorer
|   |   +-- test_tech_detector.py  Tests unitaires tech_detector
|   |   +-- test_gtm_detector.py   Tests unitaires gtm_detector
|   +-- requirements.txt      Dependances Python (FastAPI, httpx, BeautifulSoup, slowapi, pytest)
|   +-- render.yaml           Configuration Blueprint Render
|   +-- warmup.py             Script de warm-up anti-cold-start
|   +-- API_CONTRACT.md       Contrat JSON complet entre frontend et backend
|   +-- .env.example          Template des variables d'environnement
|
+-- frontend/                 Vue 3 + Vite
|   +-- src/
|   |   +-- App.vue                     Orchestrateur (phases : idle / loading / result / error)
|   |   +-- main.js                     Point d'entree Vue
|   |   +-- components/
|   |   |   +-- AppHeader.vue
|   |   |   +-- SearchForm.vue
|   |   |   +-- HistoryPanel.vue        10 dernieres analyses, persistance localStorage
|   |   |   +-- LoadingState.vue
|   |   |   +-- ErrorState.vue
|   |   |   +-- result/
|   |   |   |   +-- ResultView.vue      Conteneur + copie JSON + affichage latence
|   |   |   |   +-- ProfileCard.vue     Profil entreprise + favicon
|   |   |   |   +-- ScoreCard.vue       Score avec donut SVG
|   |   |   |   +-- GtmCard.vue         Signaux GTM
|   |   |   |   +-- TechStackCard.vue   Tech stack (section repliable)
|   +-- netlify.toml          Configuration de deploiement Netlify
|   +-- .env.example          Template des variables d'environnement
|
+-- CLAUDE.md                 Instructions pour les agents Claude Code
```

---

## Limites actuelles et pistes d'amelioration

**Cold start Render (free tier).** Le premier appel apres une periode d'inactivite prend 30 a 60 secondes. Solvable en passant sur le plan payant Render ($7/mois) ou en configurant un cron de warm-up persistant. En production reelle, ce n'est pas un probleme.

**Sites JavaScript-only non rendus.** Le scraper fetch le HTML statique. Les SPA sans SSR et les sites dont le contenu est charge entierement en AJAX retournent une page quasi vide au scraper. La solution serait d'integrer Playwright en mode optionnel, active uniquement si le HTML retourne est trop court. Non implemente ici car cela alourdit le deploiement et allonge la latence de plusieurs secondes.

**Couverture des signatures de detection.** Le catalogue couvre 130+ signatures pour la tech stack et les signaux GTM, mais de nouveaux outils ou des patterns d'integration atypiques peuvent passer inapercus. La detection est par nature partielle : elle identifie ce qu'elle reconnait, pas tout ce qui est present.

**Fiabilite du profil LLM.** Mistral produit des resultats coherents sur la grande majorite des sites, mais peut se tromper sur le secteur ou la taille estimee pour des entreprises peu documentees ou des landing pages incompletes. Le parsing defensif garantit qu'un echec LLM ne plante pas l'analyse, mais le profil partiel resultant est moins exploitable.

**Analyse limitee a la page d'accueil.** Une seule page est analysee (la racine du domaine). Une version plus avancee crawlerait les pages `/pricing`, `/about` et `/blog` pour enrichir la detection des signaux et le contexte du profiler. Cela multiplierait les appels HTTP et la latence, ce qui n'est pas justifie pour un MVP.
