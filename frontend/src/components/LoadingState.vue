<template>
  <div class="loading-screen">
    <div class="radar-wrapper">
      <div class="radar-ring ring-1"></div>
      <div class="radar-ring ring-2"></div>
      <div class="radar-dot"></div>
    </div>

    <div class="loading-text">
      <h2 class="loading-title">Analyse de {{ displayUrl }} en cours…</h2>
      <p class="loading-sub">{{ reassurance }}</p>
    </div>

    <div class="steps-card">
      <div
        v-for="(step, i) in STEPS"
        :key="step"
        class="step-row"
        :class="{ 'last-step': i === STEPS.length - 1 }"
      >
        <div class="step-icon">
          <svg v-if="i < stepIndex" width="26" height="26" viewBox="0 0 26 26">
            <circle cx="13" cy="13" r="12" fill="#6D5BD0"/>
            <path d="M8 13.2L11.3 16.5L18.2 9.2" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else-if="i === stepIndex" width="24" height="24" viewBox="0 0 24 24" class="spin">
            <circle cx="12" cy="12" r="9.5" fill="none" stroke="#EDE8FA" stroke-width="3"/>
            <path d="M12 2.5A9.5 9.5 0 0 1 21.5 12" fill="none" stroke="#6D5BD0" stroke-width="3" stroke-linecap="round"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 18 18">
            <circle cx="9" cy="9" r="7.5" fill="none" stroke="#E5E1EF" stroke-width="2.2"/>
          </svg>
        </div>
        <span
          class="step-label"
          :style="{
            fontWeight: i === stepIndex ? 700 : 600,
            color: i > stepIndex ? '#B7B0C4' : '#1E1B2E',
          }"
        >{{ step }}</span>
      </div>
    </div>

    <div class="elapsed">{{ elapsedSec }}s écoulées</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ url: { type: String, default: '' } })

const STEPS = ['Récupération du site', 'Détection technique', 'Analyse du profil', 'Calcul du score']
const STEP_DURATIONS = [3000, 2400, 2200, 2000]

const stepIndex = ref(0)
const elapsedSec = ref(0)

const displayUrl = computed(() =>
  (props.url || 'ce site').replace(/^https?:\/\//i, '').replace(/\/$/, '')
)

const reassurance = computed(() => {
  if (elapsedSec.value >= 9) return 'Finalisation du score, presque terminé…'
  if (elapsedSec.value >= 6) return 'Analyse du profil en cours, ça ne devrait plus tarder…'
  if (elapsedSec.value >= 3) return 'Le serveur se réveille (premier appel à froid), un instant…'
  return 'Connexion au site en cours…'
})

let timers = []
let elapsedTimer = null

onMounted(() => {
  elapsedTimer = setInterval(() => { elapsedSec.value++ }, 1000)
  let cumulative = 0
  STEP_DURATIONS.forEach((d, i) => {
    cumulative += d
    timers.push(setTimeout(() => { stepIndex.value = i + 1 }, cumulative))
  })
})

onBeforeUnmount(() => {
  timers.forEach(clearTimeout)
  timers = []
  if (elapsedTimer) clearInterval(elapsedTimer)
})
</script>

<style scoped>
@keyframes radarPulse {
  0%   { transform: scale(0.55); opacity: 0.9; }
  100% { transform: scale(1.9);  opacity: 0; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-screen {
  padding-top: 13vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 36px;
}

.radar-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.5px solid var(--accent);
  animation: radarPulse 1.8s ease-out infinite;
}
.ring-2 { animation-delay: .6s; }

.radar-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent);
  position: relative;
  z-index: 1;
}

.loading-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.loading-title {
  font: 600 24px var(--font-heading);
  color: var(--text);
}

.loading-sub {
  font: 500 14px/1.6 var(--font-body);
  color: var(--text-secondary);
  max-width: 380px;
}

.steps-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 6px 22px;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 15px 2px;
  border-bottom: 1px solid rgba(30,20,50,.06);
}
.last-step { border-bottom: none; }

.step-icon {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spin { animation: spin .9s linear infinite; }

.step-label { font-size: 15px; font-family: var(--font-body); }

.elapsed {
  font: 600 12.5px var(--font-body);
  color: #B7B0C4;
}
</style>
