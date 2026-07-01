<template>
  <div v-if="history.length" class="history-panel">
    <p class="history-label">Analyses récentes</p>
    <div class="history-list">
      <button
        v-for="entry in history"
        :key="entry.url"
        class="history-item"
        @click="$emit('load', entry)"
      >
        <img
          v-if="entry.favicon"
          :src="entry.favicon"
          class="history-favicon"
          alt=""
          @error="e => e.target.style.display = 'none'"
        />
        <span class="history-name">{{ entry.name }}</span>
        <span class="history-score" :class="scoreClass(entry.score)">{{ entry.score }}/100</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({ history: { type: Array, default: () => [] } })
defineEmits(['load'])

function scoreClass(score) {
  if (score >= 75) return 'score-high'
  if (score >= 50) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.history-panel {
  width: 100%;
  max-width: 540px;
  text-align: left;
}

.history-label {
  font: 700 11px var(--font-body);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  margin-bottom: 8px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  text-align: left;
  font-size: 14px;
  color: var(--text);
  transition: border-color .15s, background .15s;
}

.history-item:hover {
  border-color: var(--accent);
  background: var(--accent-bg);
}

.history-favicon {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  object-fit: contain;
  flex-shrink: 0;
}

.history-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font: 600 14px var(--font-body);
}

.history-score {
  font: 700 13px var(--font-body);
  flex-shrink: 0;
}

.score-high { color: var(--accent); }
.score-mid  { color: #B8860B; }
.score-low  { color: #B54444; }
</style>
