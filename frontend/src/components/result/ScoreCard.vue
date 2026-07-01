<template>
  <div class="card">
    <div class="score-layout">
      <div class="donut-wrapper">
        <svg width="150" height="150" viewBox="0 0 150 150">
          <circle cx="75" cy="75" r="62" fill="none" stroke="#F0EDF7" stroke-width="13"/>
          <circle
            cx="75" cy="75" r="62"
            fill="none"
            :stroke="scoreColor"
            stroke-width="13"
            stroke-linecap="round"
            :stroke-dasharray="dashArray"
            transform="rotate(-90 75 75)"
          />
        </svg>
        <div class="donut-center">
          <span class="score-number">{{ score.score }}</span>
          <span class="score-denom">/ 100</span>
        </div>
      </div>
      <div class="score-meta">
        <div class="score-tag">Score de fit B2B SaaS</div>
        <div class="score-label" :style="{ color: scoreColor }">{{ score.label }}</div>
      </div>
    </div>

    <div class="factors">
      <div v-for="factor in score.factors" :key="factor.name" class="factor">
        <div class="factor-header">
          <span class="factor-name">{{ factor.name }}</span>
          <span class="factor-pts">{{ factor.points }}/{{ factor.max }}</span>
        </div>
        <div class="factor-track">
          <div
            class="factor-fill"
            :style="{ width: factor.max > 0 ? (factor.points / factor.max * 100) + '%' : '0%' }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ score: { type: Object, required: true } })

const CIRCUMFERENCE = 2 * Math.PI * 62

const scoreColor = computed(() => {
  const s = props.score.score
  if (s >= 75) return '#6D5BD0'
  if (s >= 50) return '#B8860B'
  return '#B54444'
})

const dashArray = computed(() => {
  const dash = CIRCUMFERENCE * (props.score.score / 100)
  return `${dash.toFixed(1)} ${CIRCUMFERENCE.toFixed(1)}`
})
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px 36px;
  display: flex;
  flex-direction: column;
  gap: 34px;
}

.score-layout {
  display: flex;
  gap: 36px;
  align-items: center;
  flex-wrap: wrap;
}

.donut-wrapper {
  position: relative;
  width: 150px;
  height: 150px;
  flex-shrink: 0;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-number {
  font: 700 38px var(--font-heading);
  color: var(--text);
  line-height: 1;
}

.score-denom {
  font: 700 11px var(--font-body);
  color: var(--text-muted);
  letter-spacing: .06em;
  margin-top: 2px;
}

.score-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 180px;
}

.score-tag {
  font: 700 11px var(--font-body);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: .09em;
}

.score-label { font: 600 23px var(--font-heading); }

.factors {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor { display: flex; flex-direction: column; gap: 7px; }

.factor-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.factor-name { font: 600 13.5px var(--font-body); color: #3A3448; }
.factor-pts  { font: 700 13px var(--font-body); color: var(--text-secondary); flex-shrink: 0; }

.factor-track {
  height: 6px;
  background: #F0EDF7;
  border-radius: 999px;
  overflow: hidden;
}

.factor-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 999px;
  transition: width .4s ease;
}

@media (max-width: 480px) {
  .card { padding: 28px 20px; }
}
</style>
