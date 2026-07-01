<template>
  <div class="card">
    <div class="card-header" @click="expanded = !expanded">
      <div class="card-tag">Stack technique</div>
      <svg
        width="14" height="14" viewBox="0 0 14 14"
        :style="{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .2s' }"
      >
        <path d="M3 5L7 9L11 5" stroke="#9992A6" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <div v-if="expanded" class="tech-groups">
      <div v-for="group in techGroups" :key="group.key" class="tech-group">
        <div class="group-label">{{ group.label }}</div>
        <div class="pills">
          <span v-for="item in group.items" :key="item" class="pill">{{ item }}</span>
        </div>
      </div>
      <p v-if="!techGroups.length" class="empty">Aucune technologie détectée</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ tech: { type: Object, required: true } })

const expanded = ref(false)

const LABELS = {
  frameworks: 'Frameworks',
  cdn: 'CDN',
  cms: 'CMS',
  server: 'Serveur',
  analytics: 'Analytics',
  tag_managers: 'Tag managers',
  other: 'Autres',
}

const techGroups = computed(() =>
  Object.entries(LABELS)
    .map(([key, label]) => ({ key, label, items: props.tech[key] ?? [] }))
    .filter(g => g.items.length)
)
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 26px 36px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.card-tag {
  font: 700 11px var(--font-body);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: .09em;
}

.tech-groups { display: flex; flex-direction: column; gap: 16px; }
.tech-group  { display: flex; flex-direction: column; gap: 8px; }

.group-label { font: 700 12.5px var(--font-body); color: var(--text-secondary); }

.pills { display: flex; flex-wrap: wrap; gap: 8px; }

.pill {
  background: var(--surface);
  color: #5C5568;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 5px 12px;
  font: 600 12.5px var(--font-body);
}

.empty { font: 500 14px var(--font-body); color: var(--text-muted); }

@media (max-width: 480px) {
  .card { padding: 20px 20px; }
}
</style>
