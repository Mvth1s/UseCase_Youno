# Konsole Company Analyzer - Frontend

Interface Vue 3 + Vite de l'analyseur d'entreprises Konsole.

## Stack

- **Vue 3** (Composition API, `<script setup>`)
- **Vite** : build et dev server
- **Google Fonts** : Manrope (corps) + Source Serif 4 (titres)

## Architecture

`App.vue` est l'orchestrateur pur : il gère la machine d'état (`idle → loading → result → error`) et l'historique, sans logique de rendu. Chaque composant a une responsabilité unique.

```
src/
  App.vue                      # Orchestrateur (phase, historique, fetch)
  style.css                    # Design tokens globaux (variables CSS)
  components/
    AppHeader.vue              # Logo + tagline
    SearchForm.vue             # Search pill avec validation
    HistoryPanel.vue           # Historique localStorage (10 entrées)
    LoadingState.vue           # Stepper 4 étapes + animation radar + elapsed
    ErrorState.vue             # Mapping HTTP status → message lisible
    result/
      ResultView.vue           # Assembleur des 4 cards résultat
      ProfileCard.vue          # Avatar favicon, badges, copie JSON, latency
      ScoreCard.vue            # Donut SVG + barres par facteur
      GtmCard.vue              # Chips outils + présence pricing/demo/careers
      TechStackCard.vue        # Liste dépliable par catégorie
```

## Variables d'environnement

| Variable | Usage |
|---|---|
| `VITE_API_URL` | URL du backend FastAPI (ex. `https://mon-backend.onrender.com`) |

```bash
cp .env.example .env.local
# Renseigner VITE_API_URL
```

## Lancement local

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # Build de production dans dist/
```

## Déploiement

Déployé sur **Netlify** via le dossier `frontend/`. Variable `VITE_API_URL` à configurer dans les settings Netlify.
