<template>
  <div class="app-shell">
    <AppHeader />

    <main class="app-content">
      <!-- Idle -->
      <div v-if="phase === 'idle'" class="idle-screen">
        <h1 class="hero-title">Comprenez n'importe quelle entreprise<br>en un coup d'œil</h1>
        <p class="hero-sub">Collez l'URL d'un site pour obtenir un profil structuré et un score de fit B2B SaaS en quelques secondes.</p>
        <SearchForm v-model="url" :input-error="inputError" @submit="handleAnalyze" />
        <HistoryPanel :history="history" @load="loadFromHistory" />
      </div>

      <!-- Chargement -->
      <LoadingState v-else-if="phase === 'loading'" :url="url" />

      <!-- Résultat -->
      <ResultView
        v-else-if="phase === 'result'"
        :result="result"
        :latency="latency"
        @new-search="startNewSearch"
      />

      <!-- Erreur -->
      <ErrorState
        v-else-if="phase === 'error'"
        :error-info="errorInfo"
        @retry="startNewSearch"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppHeader   from './components/AppHeader.vue'
import SearchForm  from './components/SearchForm.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import LoadingState from './components/LoadingState.vue'
import ErrorState  from './components/ErrorState.vue'
import ResultView  from './components/result/ResultView.vue'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// État global
// ---------------------------------------------------------------------------
const phase      = ref('idle')   // 'idle' | 'loading' | 'result' | 'error'
const url        = ref('')
const inputError = ref(null)
const result     = ref(null)
const latency    = ref(null)
const errorInfo  = ref(null)     // { status: number, detail: string }

// ---------------------------------------------------------------------------
// Historique localStorage
// ---------------------------------------------------------------------------
const HISTORY_KEY = 'konsole_history'
const HISTORY_MAX = 10
const history = ref([])

function loadHistory() {
  try { history.value = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]') }
  catch { history.value = [] }
}

function saveToHistory(data) {
  const entry = {
    url:    data.url,
    name:   data.profile?.name ?? data.page_title ?? data.url,
    score:  data.score?.score ?? 0,
    favicon: data.favicon_url ?? null,
    result: data,
  }
  const deduped = history.value.filter(h => h.url !== entry.url)
  history.value = [entry, ...deduped].slice(0, HISTORY_MAX)
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value)) }
  catch { /* localStorage plein */ }
}

function loadFromHistory(entry) {
  result.value   = entry.result
  url.value      = entry.url
  latency.value  = null
  errorInfo.value = null
  phase.value    = 'result'
}

function startNewSearch() {
  phase.value     = 'idle'
  url.value       = ''
  inputError.value = null
  result.value    = null
  latency.value   = null
  errorInfo.value = null
}

// ---------------------------------------------------------------------------
// Analyse principale
// ---------------------------------------------------------------------------
async function handleAnalyze() {
  const trimmed = url.value.trim()
  if (!trimmed) {
    inputError.value = 'Merci de saisir une URL à analyser.'
    return
  }
  inputError.value = null
  phase.value  = 'loading'
  result.value = null
  latency.value = null

  const startTime  = Date.now()
  const controller = new AbortController()
  const timeoutId  = setTimeout(() => controller.abort(), 60_000)

  try {
    const response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: trimmed }),
      signal: controller.signal,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      errorInfo.value = { status: response.status, detail: body.detail ?? `Erreur HTTP ${response.status}` }
      phase.value = 'error'
      return
    }

    result.value  = await response.json()
    latency.value = ((Date.now() - startTime) / 1000).toFixed(1)
    saveToHistory(result.value)
    phase.value = 'result'
  } catch (err) {
    errorInfo.value = err.name === 'AbortError'
      ? { status: 408, detail: 'La requête a dépassé 60 secondes. Le backend est peut-être en cours de démarrage. Réessayez.' }
      : { status: 0,   detail: err.message ?? 'Erreur inconnue.' }
    phase.value = 'error'
  } finally {
    clearTimeout(timeoutId)
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-content {
  max-width: 760px;
  margin: 0 auto;
  padding: 0 24px 80px;
  width: 100%;
  box-sizing: border-box;
}

.idle-screen {
  padding-top: 13vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 28px;
}

.hero-title {
  font: 600 42px/1.2 var(--font-heading);
  color: var(--text);
  max-width: 580px;
  letter-spacing: -0.01em;
}

.hero-sub {
  font: 500 16px/1.6 var(--font-body);
  color: var(--text-secondary);
  max-width: 460px;
}

@media (max-width: 480px) {
  .hero-title { font-size: 28px; }
  .hero-sub   { font-size: 15px; }
  .app-content { padding: 0 16px 60px; }
}
</style>
