<template>
  <div class="card">
    <div class="card-tag">Signaux GTM</div>

    <div v-if="chipGroups.length" class="chip-groups">
      <div v-for="group in chipGroups" :key="group.label" class="chip-group">
        <div class="group-label">{{ group.label }}</div>
        <div class="chips">
          <span v-for="item in group.items" :key="item" class="chip">{{ item }}</span>
        </div>
      </div>
    </div>

    <div class="presence-grid">
      <div v-for="item in presenceItems" :key="item.label" class="presence-item">
        <div class="presence-icon" :class="item.present ? 'icon-yes' : 'icon-no'">
          <svg v-if="item.present" width="13" height="13" viewBox="0 0 13 13">
            <path d="M2.2 6.8L5 9.6L10.8 3.4" stroke="#1F9D68" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="11" height="11" viewBox="0 0 11 11">
            <path d="M1.8 1.8L9.2 9.2M9.2 1.8L1.8 9.2" stroke="#B54444" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="presence-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ gtm: { type: Object, required: true } })

const chipGroups = computed(() => [
  { label: 'Outils de chat',       items: props.gtm.chat_tools ?? [] },
  { label: 'Pixels publicitaires', items: props.gtm.ad_pixels ?? [] },
  { label: "Outils d'analytics",   items: props.gtm.analytics_tools ?? [] },
].filter(g => g.items.length))

const presenceItems = computed(() => [
  { label: 'Page pricing',    present: props.gtm.has_pricing_page },
  { label: 'Formulaire demo', present: props.gtm.has_demo_form },
  { label: 'Page careers',    present: props.gtm.has_careers_page },
])
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 32px 36px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.card-tag {
  font: 700 11px var(--font-body);
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: .09em;
}

.chip-groups { display: flex; flex-direction: column; gap: 16px; }

.chip-group { display: flex; flex-direction: column; gap: 10px; }

.group-label { font: 700 13px var(--font-body); color: #5C5568; }

.chips { display: flex; flex-wrap: wrap; gap: 8px; }

.chip {
  background: var(--accent-bg);
  color: var(--accent-dark);
  border: 1px solid var(--accent-border);
  border-radius: 999px;
  padding: 6px 14px;
  font: 700 12.5px var(--font-body);
}

.presence-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(30,20,50,.06);
}

.presence-item { display: flex; align-items: center; gap: 10px; }

.presence-icon {
  width: 23px;
  height: 23px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-yes { background: #E7F5EC; }
.icon-no  { background: #F5EDED; }

.presence-label { font: 600 13.5px var(--font-body); color: #3A3448; }

@media (max-width: 480px) {
  .card { padding: 24px 20px; }
  .presence-grid { grid-template-columns: 1fr; gap: 12px; }
}
</style>
