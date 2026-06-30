# Youno / Konsole - Company Analyzer

Application web qui analyse un site (ex. `stripe.com`) et renvoie : nom, description, tech stack, signaux GTM, secteur, taille, et un score "fit B2B SaaS".

## Presentation

Pipeline sequentielle cote serveur : collecte HTTP (httpx + BeautifulSoup) → detection tech stack → detection signaux GTM → profiling LLM (Mistral) → scoring pondere. Un seul appel LLM dans toute la chaine pour maitriser cout, latence et risque de panne.

## Architecture

```
UseCase_Youno/
  backend/         FastAPI (Python 3.11)
    app/
      main.py      Route POST /analyze + CORS + orchestration pipeline
      scraper.py   Fetch httpx + extraction BeautifulSoup
      tech_detector.py  Detection stack (HTML + headers)
      gtm_detector.py   Detection signaux GTM (chat, pixels, analytics)
      profiler.py  Appel Mistral, JSON force, parsing defensif
      scorer.py    Score pondere "fit B2B SaaS" explicable
      models.py    Modeles Pydantic entree/sortie
  frontend/        Vue 3 + Vite
    src/App.vue    Interface principale
```

## Lancement local

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # renseigner MISTRAL_API_KEY
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # VITE_API_URL=http://localhost:8000
npm run dev                    # http://localhost:5173
```

## Deploiement

### Ordre obligatoire

Deployer le backend Render en premier, puis le frontend Netlify, puis revenir sur Render pour injecter l'URL Netlify dans ALLOWED_ORIGINS.

### Backend (Render)

1. Aller sur [render.com](https://render.com) → **New** → **Web Service** → connecter le repo GitHub `Mvth1s/UseCase_Youno`.
2. Render detecte `backend/render.yaml` automatiquement (Blueprint). Si ce n'est pas le cas, renseigner manuellement :
   - **Root directory** : `backend`
   - **Build command** : `pip install -r requirements.txt`
   - **Start command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path** : `/health`
3. Dans l'onglet **Environment** du service, ajouter les variables :
   - `MISTRAL_API_KEY` : votre cle API Mistral
   - `ALLOWED_ORIGINS` : laisser vide pour l'instant (a remplir apres le deploiement Netlify)
   - `PYTHON_VERSION` : `3.11.0`
4. Cliquer **Deploy**. Copier l'URL generee, ex. `https://konsole-analyzer-backend.onrender.com`.

### Frontend (Netlify)

1. Aller sur [netlify.com](https://netlify.com) → **Add new site** → **Import from Git** → connecter le repo GitHub.
2. Netlify detecte `frontend/netlify.toml`. Verifier les parametres :
   - **Base directory** : `frontend`
   - **Build command** : `npm run build`
   - **Publish directory** : `frontend/dist`
3. Dans **Site configuration** → **Environment variables**, ajouter :
   - `VITE_API_URL` : l'URL Render copiee a l'etape precedente (ex. `https://konsole-analyzer-backend.onrender.com`)
4. Cliquer **Deploy site**. Copier l'URL generee, ex. `https://konsole-analyzer.netlify.app`.

### Finalisation CORS

1. Retourner sur Render → **Environment** du service backend.
2. Mettre a jour `ALLOWED_ORIGINS` avec l'URL Netlify exacte (ex. `https://konsole-analyzer.netlify.app`).
3. Cliquer **Save changes** → Render redeploit automatiquement.

### Verification de bout en bout

```bash
# Health check backend
curl https://konsole-analyzer-backend.onrender.com/health

# Test analyze
curl -X POST https://konsole-analyzer-backend.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "stripe.com"}'
```

## Cold start Render (free tier)

Le free tier Render endort les services apres 15 minutes d'inactivite. Le premier appel apres une periode de sommeil prend 30 a 60 secondes.

**Mitigation : script de warm-up**

```bash
python backend/warmup.py https://konsole-analyzer-backend.onrender.com
```

Ce script ping `/health` toutes les 14 minutes. Il peut tourner localement ou etre configure comme cron sur [cron-job.org](https://cron-job.org) (gratuit).

Alternative sans hebergement : configurer un moniteur gratuit sur [UptimeRobot](https://uptimerobot.com) avec une frequence de 5 minutes sur l'URL `/health`.

Le frontend affiche un etat de chargement explicite pour absorber ce delai cote utilisateur.

## Choix techniques

- **Un seul appel LLM** (Mistral) dans toute la chaine : maitrise du cout et de la latence.
- **httpx synchrone** dans le scraper : suffisant pour un endpoint unitaire, evite la complexite async.
- **Pydantic v2** pour les modeles entree/sortie : validation stricte, serialisation JSON fiable.
- **CORS configurable par variable d'environnement** : pas de domaine harde en dur dans le code.

## Limites connues

- Le free tier Render entraine un cold start (voir ci-dessus).
- Les sites avec protection anti-bot (Cloudflare, etc.) peuvent retourner un contenu vide ou une erreur 503.
- L'analyse LLM peut varier selon la reponse du modele ; le parsing defensif garantit un fallback propre.

## Sens produit

Cet outil repond au besoin d'un commercial Konsole qui veut qualifier rapidement un prospect : est-ce un SaaS B2B ? Quelle stack utilisent-ils ? Ont-ils deja investi dans le marketing (pixels, chat) ? Le score synthetise ces signaux en un chiffre actionnable.
