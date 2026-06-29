<template>
  <div class="app">
    <header class="app-header">
      <h1>Konsole Company Analyzer</h1>
      <p class="subtitle">Entrez l'URL d'un site pour obtenir son profil, sa tech stack et ses signaux GTM.</p>
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
        <p>Analyse en cours... (peut prendre 30s au premier appel)</p>
      </div>

      <!-- Message d'erreur -->
      <div v-if="error && !loading" class="error-block" role="alert">
        <strong>Erreur :</strong> {{ error }}
      </div>

      <!-- Resultat brut JSON -->
      <div v-if="result && !loading" class="result-block">
        <h2>Resultat</h2>
        <pre class="result-json">{{ JSON.stringify(result, null, 2) }}</pre>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

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
</script>

<style scoped>
.app {
  font-family: 'Segoe UI', system-ui, sans-serif;
  max-width: 860px;
  margin: 0 auto;
  padding: 2rem 1rem;
  color: #1a1a2e;
}

.app-header {
  margin-bottom: 2rem;
  text-align: center;
}

.app-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
}

.subtitle {
  color: #555;
  font-size: 0.95rem;
}

.search-form {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
}

.url-input {
  flex: 1;
  padding: 0.6rem 0.9rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  outline: none;
}

.url-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.analyze-btn {
  padding: 0.6rem 1.4rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.analyze-btn:hover:not(:disabled) {
  background: #4f46e5;
}

.analyze-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.loading-block {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  background: #f0f4ff;
  border-radius: 8px;
  color: #4f46e5;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #c7d2fe;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-block {
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  color: #b91c1c;
  margin-bottom: 1rem;
}

.result-block h2 {
  font-size: 1.1rem;
  margin-bottom: 0.6rem;
}

.result-json {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.82rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}
</style>
