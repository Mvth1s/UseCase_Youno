<template>
  <div class="app">
    <header class="app-header">
      <h1 class="app-title">Konsole <span class="title-dot">·</span> Company Analyzer</h1>
      <p class="subtitle">Analysez n'importe quel site : profil entreprise, tech stack et signaux GTM en quelques secondes.</p>
    </header>

    <main class="app-main">

      <!-- Formulaire de saisie -->
      <form class="search-form" @submit.prevent="handleAnalyze">
        <input
          v-model="url"
          type="text"
          placeholder="ex. stripe.com"
          class="url-input"
          :disabled="loading"
          aria-label="URL du site a analyser"
        />
        <button type="submit" class="analyze-btn" :disabled="loading || !url.trim()">
          {{ loading ? 'Analyse...' : 'Analyser' }}
        </button>
      </form>

      <!-- Etat loading -->
      <div v-if="loading" class="loading-block" role="status" aria-live="polite">
        <div class="spinner" aria-hidden="true"></div>
        <div class="loading-text">
          <p class="loading-main">Analyse en cours...</p>
          <p class="loading-sub">Le premier appel peut prendre ~30s (cold start Render)</p>
        </div>
      </div>

      <!-- Message d'erreur -->
      <div v-if="error && !loading" class="error-block" role="alert">
        <strong>Erreur :</strong> {{ error }}
      </div>

      <!-- Resultats -->
      <div v-if="result && !loading" class="results">

        <!-- Section A : Identite -->
        <section class="card section-identity">
          <div class="identity-header">
            <img
              v-if="result.favicon_url"
              :src="result.favicon_url"
              class="favicon"
              alt=""
              @error="hideFavicon"
            />
            <h2 class="company-name">{{ result.profile?.name ?? result.page_title }}</h2>
          </div>
          <p v-if="result.profile?.description" class="company-desc">{{ result.profile.description }}</p>
          <div class="badges-row">
            <span v-if="result.profile?.sector" class="badge badge-neutral">{{ result.profile.sector }}</span>
            <span v-if="result.profile?.estimated_size" class="badge badge-neutral">{{ result.profile.estimated_size }}</span>
            <span
              v-if="result.profile?.audience"
              class="badge"
              :class="audienceBadgeClass(result.profile.audience)"
            >{{ result.profile.audience }}</span>
          </div>
          <a
            v-if="result.url"
            :href="result.url"
            target="_blank"
            rel="noopener noreferrer"
            class="result-url"
          >{{ result.url }}</a>
        </section>

        <!-- Grille deux colonnes (tech + GTM) sur desktop -->
        <div class="two-col">

          <!-- Section B : Tech Stack -->
          <section class="card section-tech">
            <h2 class="section-title">Stack technique</h2>
            <div v-if="hasTechStack" class="tech-categories">
              <div v-for="cat in techCategories" :key="cat.key" class="tech-cat">
                <span class="cat-label">{{ cat.label }}</span>
                <div class="pills-row">
                  <span v-for="item in cat.items" :key="item" class="pill pill-default">{{ item }}</span>
                </div>
              </div>
            </div>
            <p v-else class="empty-msg">Aucune technologie detectee</p>
          </section>

          <!-- Section C : Signaux GTM -->
          <section class="card section-gtm">
            <div class="section-title-row">
              <h2 class="section-title">Signaux GTM</h2>
              <span class="badge-insight">KEY INSIGHT</span>
            </div>

            <div class="gtm-groups">
              <div class="gtm-group">
                <span class="cat-label">Outils de chat</span>
                <div v-if="result.gtm_signals?.chat_tools?.length" class="pills-row">
                  <span v-for="t in result.gtm_signals.chat_tools" :key="t" class="pill pill-chat">{{ t }}</span>
                </div>
                <p v-else class="empty-msg">Aucun detecte</p>
              </div>

              <div class="gtm-group">
                <span class="cat-label">Pixels publicitaires</span>
                <div v-if="result.gtm_signals?.ad_pixels?.length" class="pills-row">
                  <span v-for="t in result.gtm_signals.ad_pixels" :key="t" class="pill pill-pixel">{{ t }}</span>
                </div>
                <p v-else class="empty-msg">Aucun detecte</p>
              </div>

              <div class="gtm-group">
                <span class="cat-label">Analytics</span>
                <div v-if="result.gtm_signals?.analytics_tools?.length" class="pills-row">
                  <span v-for="t in result.gtm_signals.analytics_tools" :key="t" class="pill pill-analytics">{{ t }}</span>
                </div>
                <p v-else class="empty-msg">Aucun detecte</p>
              </div>
            </div>

            <div class="gtm-booleans">
              <span class="bool-indicator" :class="result.gtm_signals?.has_pricing_page ? 'bool-true' : 'bool-false'">
                {{ result.gtm_signals?.has_pricing_page ? '✓' : '✗' }} Page Pricing
              </span>
              <span class="bool-indicator" :class="result.gtm_signals?.has_demo_form ? 'bool-true' : 'bool-false'">
                {{ result.gtm_signals?.has_demo_form ? '✓' : '✗' }} Formulaire Demo
              </span>
              <span class="bool-indicator" :class="result.gtm_signals?.has_careers_page ? 'bool-true' : 'bool-false'">
                {{ result.gtm_signals?.has_careers_page ? '✓' : '✗' }} Page Careers
              </span>
            </div>
          </section>

        </div>

        <!-- Section D : Score B2B SaaS -->
        <section class="card section-score">
          <h2 class="section-title">Score Fit B2B SaaS</h2>

          <div class="score-header">
            <div class="score-number-block">
              <span class="score-number" :class="scoreColorClass(result.score?.score)">
                {{ result.score?.score ?? 0 }}
              </span>
              <span class="score-denom">/100</span>
            </div>
            <span class="score-label" :class="scoreColorClass(result.score?.score)">
              {{ result.score?.label }}
            </span>
          </div>

          <div class="progress-bar-outer">
            <div
              class="progress-bar-inner"
              :class="scoreColorClass(result.score?.score)"
              :style="{ width: (result.score?.score ?? 0) + '%' }"
            ></div>
          </div>

          <div v-if="result.score?.factors?.length" class="score-factors">
            <div v-for="factor in result.score.factors" :key="factor.name" class="factor-row">
              <span class="factor-name">{{ factor.name }}</span>
              <div class="factor-bar-outer">
                <div
                  class="factor-bar-inner"
                  :style="{ width: factor.max > 0 ? (factor.points / factor.max * 100) + '%' : '0%' }"
                ></div>
              </div>
              <span class="factor-pts">{{ factor.points }} / {{ factor.max }} pts</span>
            </div>
          </div>
        </section>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// URL de l'API lue depuis la variable d'environnement Vite.
// Copier frontend/.env.example en frontend/.env.local et renseigner VITE_API_URL.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const url = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref(null)

async function handleAnalyze() {
  if (!url.value.trim()) return

  loading.value = true
  result.value = null
  error.value = null

  // Timeout de 60 secondes pour absorber le cold start Render (free tier)
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60_000)

  try {
    const response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.value.trim() }),
      signal: controller.signal,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail ?? `Erreur HTTP ${response.status}`)
    }

    result.value = await response.json()
  } catch (err) {
    if (err.name === 'AbortError') {
      error.value = 'La requete a depasse 60 secondes. Le backend (Render free tier) est peut-etre en cours de demarrage - reessayez dans un instant.'
    } else {
      error.value = err.message ?? 'Erreur inconnue.'
    }
  } finally {
    clearTimeout(timeoutId)
    loading.value = false
  }
}

// Cache les favicons en erreur de chargement
function hideFavicon(event) {
  event.target.style.display = 'none'
}

// Mapping cles tech_stack -> labels lisibles
const TECH_CAT_LABELS = {
  frameworks: 'Frameworks',
  cdn: 'CDN',
  cms: 'CMS',
  server: 'Serveur',
  analytics: 'Analytics',
  tag_managers: 'Tag Managers',
  other: 'Autres',
}

// Retourne uniquement les categories de tech non vides
const techCategories = computed(() => {
  const stack = result.value?.tech_stack ?? {}
  return Object.entries(TECH_CAT_LABELS)
    .map(([key, label]) => ({ key, label, items: stack[key] ?? [] }))
    .filter((cat) => cat.items.length > 0)
})

const hasTechStack = computed(() => techCategories.value.length > 0)

// Classe CSS du badge audience selon la valeur B2B/B2C/mixed
function audienceBadgeClass(audience) {
  if (!audience) return 'badge-neutral'
  const a = audience.toLowerCase()
  if (a === 'b2b') return 'badge-b2b'
  if (a === 'b2c') return 'badge-b2c'
  return 'badge-neutral'
}

// Classe CSS couleur selon le score numerique
function scoreColorClass(score) {
  if (score == null) return 'score-gray'
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-blue'
  if (score >= 40) return 'score-orange'
  return 'score-red'
}
</script>

<style scoped>
/* -----------------------------------------------
   Layout principal
----------------------------------------------- */
.app {
  max-width: 820px;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 4rem;
  text-align: left;
}

/* -----------------------------------------------
   Header
----------------------------------------------- */
.app-header {
  margin-bottom: 2rem;
  text-align: center;
}

.app-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-h);
  margin: 0 0 0.4rem;
  letter-spacing: -0.02em;
}

.title-dot {
  color: var(--accent);
}

.subtitle {
  color: var(--text);
  font-size: 0.95rem;
  margin: 0;
}

/* -----------------------------------------------
   Formulaire
----------------------------------------------- */
.search-form {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
}

.url-input {
  flex: 1;
  padding: 0.6rem 0.9rem;
  font-size: 1rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  outline: none;
  background: var(--bg);
  color: var(--text-h);
  font-family: inherit;
  transition: border-color 0.15s;
}

.url-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(170, 59, 255, 0.15);
}

.analyze-btn {
  padding: 0.6rem 1.4rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
}

.analyze-btn:hover:not(:disabled) {
  opacity: 0.88;
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* -----------------------------------------------
   Loading
----------------------------------------------- */
.loading-block {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 1rem 1.2rem;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  border-radius: 8px;
  color: var(--text-h);
  margin-bottom: 1rem;
}

.loading-text {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.loading-main {
  font-weight: 600;
  color: var(--text-h);
  margin: 0;
}

.loading-sub {
  font-size: 0.85rem;
  color: var(--text);
  margin: 0;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
  flex-shrink: 0;
  margin-top: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* -----------------------------------------------
   Erreur
----------------------------------------------- */
.error-block {
  padding: 1rem 1.2rem;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  color: #b91c1c;
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

/* -----------------------------------------------
   Resultats generaux
----------------------------------------------- */
.results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem 1.4rem;
  background: var(--bg);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-h);
  margin: 0 0 0.9rem;
  letter-spacing: 0.01em;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.9rem;
}

.section-title-row .section-title {
  margin-bottom: 0;
}

/* -----------------------------------------------
   Section A : Identite
----------------------------------------------- */
.identity-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}

.favicon {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  object-fit: contain;
  flex-shrink: 0;
}

.company-name {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-h);
  margin: 0;
  letter-spacing: -0.02em;
}

.company-desc {
  font-style: italic;
  color: var(--text);
  font-size: 0.92rem;
  line-height: 1.5;
  margin: 0 0 0.85rem;
}

.badges-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.result-url {
  font-size: 0.8rem;
  color: var(--text);
  text-decoration: none;
  border-bottom: 1px solid var(--border);
  transition: color 0.15s;
}

.result-url:hover {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* -----------------------------------------------
   Badges generaux
----------------------------------------------- */
.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1.4;
}

.badge-neutral {
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
}

.badge-b2b {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.badge-b2c {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fed7aa;
}

.badge-insight {
  display: inline-block;
  padding: 0.18rem 0.5rem;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
  text-transform: uppercase;
  flex-shrink: 0;
}

/* -----------------------------------------------
   Grille deux colonnes
----------------------------------------------- */
.two-col {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .two-col {
    grid-template-columns: 1fr 1fr;
  }
}

/* -----------------------------------------------
   Section B : Tech Stack
----------------------------------------------- */
.tech-categories {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tech-cat {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.cat-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.pill {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 500;
}

.pill-default {
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
}

.empty-msg {
  font-size: 0.85rem;
  color: var(--text);
  font-style: italic;
  margin: 0.2rem 0 0;
}

/* -----------------------------------------------
   Section C : Signaux GTM
----------------------------------------------- */
.gtm-groups {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.gtm-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

/* Couleurs des pills GTM */
.pill-chat {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.pill-pixel {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
}

.pill-analytics {
  background: #faf5ff;
  color: #7c3aed;
  border: 1px solid #ddd6fe;
}

/* Indicateurs booleens */
.gtm-booleans {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
}

.bool-indicator {
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
}

.bool-true {
  background: #dcfce7;
  color: #166534;
}

.bool-false {
  background: #fef2f2;
  color: #b91c1c;
}

/* -----------------------------------------------
   Section D : Score
----------------------------------------------- */
.score-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.score-number-block {
  display: flex;
  align-items: baseline;
  gap: 0.15rem;
}

.score-number {
  font-size: 2.8rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
}

.score-denom {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text);
}

.score-label {
  font-size: 0.9rem;
  font-weight: 600;
}

/* Couleurs du score */
.score-green { color: #16a34a; }
.score-blue  { color: #2563eb; }
.score-orange { color: #ea580c; }
.score-red   { color: #dc2626; }
.score-gray  { color: var(--text); }

/* Barre de progression principale */
.progress-bar-outer {
  width: 100%;
  height: 8px;
  background: var(--code-bg);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 1.25rem;
}

.progress-bar-inner {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;
}

.progress-bar-inner.score-green  { background: #16a34a; }
.progress-bar-inner.score-blue   { background: #2563eb; }
.progress-bar-inner.score-orange { background: #ea580c; }
.progress-bar-inner.score-red    { background: #dc2626; }
.progress-bar-inner.score-gray   { background: var(--text); }

/* Breakdown des facteurs */
.score-factors {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.factor-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 0.75rem;
}

.factor-name {
  font-size: 0.85rem;
  color: var(--text-h);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.factor-bar-outer {
  width: 80px;
  height: 5px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
  flex-shrink: 0;
}

.factor-bar-inner {
  height: 100%;
  background: var(--accent);
  border-radius: 99px;
  transition: width 0.3s ease;
}

.factor-pts {
  font-size: 0.78rem;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  flex-shrink: 0;
}

/* -----------------------------------------------
   Responsive mobile
----------------------------------------------- */
@media (max-width: 480px) {
  .app {
    padding: 1.5rem 1rem 3rem;
  }

  .app-title {
    font-size: 1.4rem;
  }

  .search-form {
    flex-direction: column;
  }

  .analyze-btn {
    width: 100%;
  }

  .factor-row {
    grid-template-columns: 1fr auto;
  }

  .factor-bar-outer {
    display: none;
  }
}
</style>
