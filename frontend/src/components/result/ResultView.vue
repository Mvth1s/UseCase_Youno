<template>
  <div class="result-screen">
    <div class="result-meta">
      <span class="meta-text">
        Analyse effectuée pour <strong>{{ result.url }}</strong>
      </span>
      <button class="new-search-btn" @click="$emit('new-search')">Nouvelle analyse</button>
    </div>

    <ProfileCard :result="result" :latency="latency" />
    <ScoreCard :score="result.score" />
    <GtmCard :gtm="result.gtm_signals" />
    <TechStackCard :tech="result.tech_stack" />
  </div>
</template>

<script setup>
import ProfileCard from './ProfileCard.vue'
import ScoreCard from './ScoreCard.vue'
import GtmCard from './GtmCard.vue'
import TechStackCard from './TechStackCard.vue'

defineProps({
  result: { type: Object, required: true },
  latency: { type: String, default: null },
})
defineEmits(['new-search'])
</script>

<style scoped>
.result-screen {
  padding-top: 44px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 80px;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-text { font: 500 12.5px var(--font-body); color: var(--text-muted); }
.meta-text strong { color: #5C5568; }

.new-search-btn {
  background: none;
  border: none;
  color: var(--accent);
  font: 700 13px var(--font-body);
  padding: 4px 0;
  transition: opacity .15s;
}
.new-search-btn:hover { opacity: .75; }
</style>
