<template>
  <div class="card">
    <div class="profile-layout">
      <div class="avatar" aria-hidden="true">
        <span class="avatar-initial">{{ initial }}</span>
      </div>
      <div class="profile-content">
        <div class="profile-headline">
          <h2 class="company-name">{{ result.profile?.name ?? result.page_title }}</h2>
          <a
            v-if="result.url"
            :href="result.url"
            target="_blank"
            rel="noopener noreferrer"
            class="result-url"
          >{{ result.url }}</a>
        </div>

        <p v-if="latency" class="latency">Analyse en {{ latency }}s</p>

        <p v-if="result.profile?.description" class="company-desc">
          {{ result.profile.description }}
        </p>

        <div class="badges">
          <div v-if="result.profile?.sector" class="badge badge-neutral">
            <svg width="13" height="13" viewBox="0 0 13 13">
              <rect x="1.5" y="1.5" width="10" height="10" rx="1.5" fill="none" stroke="#6B6478" stroke-width="1.2"/>
              <rect x="3.7" y="3.7" width="2" height="2" fill="#6B6478"/>
              <rect x="7.3" y="3.7" width="2" height="2" fill="#6B6478"/>
              <rect x="3.7" y="7.3" width="2" height="2" fill="#6B6478"/>
            </svg>
            <span>{{ result.profile.sector }}</span>
          </div>
          <div v-if="result.profile?.estimated_size" class="badge badge-neutral">
            <svg width="13" height="13" viewBox="0 0 13 13">
              <rect x="1.5" y="7" width="2.4" height="4.5" fill="#6B6478"/>
              <rect x="5.3" y="4" width="2.4" height="7.5" fill="#6B6478"/>
              <rect x="9.1" y="1.5" width="2.4" height="10" fill="#6B6478"/>
            </svg>
            <span>{{ result.profile.estimated_size }}</span>
          </div>
          <div v-if="result.profile?.audience" class="badge" :class="audienceBadgeClass">
            {{ result.profile.audience }}
          </div>
        </div>

        <button class="copy-btn" @click="copyJson">
          {{ copySuccess ? 'Copié !' : 'Copier JSON' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  result: { type: Object, required: true },
  latency: { type: String, default: null },
})

const copySuccess = ref(false)

const initial = computed(() => {
  const name = props.result.profile?.name ?? props.result.page_title ?? ''
  return name.charAt(0).toUpperCase() || '?'
})

const audienceBadgeClass = computed(() => {
  const a = (props.result.profile?.audience ?? '').toLowerCase()
  if (a === 'b2b') return 'badge-b2b'
  if (a === 'b2c') return 'badge-b2c'
  return 'badge-mixed'
})

async function copyJson() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(props.result, null, 2))
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch {
    // navigator.clipboard indisponible (HTTP sans TLS ou permissions refusées)
  }
}
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 32px 36px;
}

.profile-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6D5BD0, #4F3FA6);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-initial {
  font: 700 20px var(--font-heading);
  color: #fff;
}

.profile-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.profile-headline {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.company-name { font: 600 24px var(--font-heading); color: var(--text); }

.result-url {
  font: 500 13px var(--font-body);
  color: var(--text-muted);
  text-decoration: none;
  transition: color .15s;
}
.result-url:hover { color: var(--accent); }

.latency {
  font: 500 12px var(--font-body);
  color: var(--text-muted);
}

.company-desc {
  font: 500 14px/1.6 var(--font-body);
  color: #5C5568;
  max-width: 540px;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.badge {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 6px 12px 6px 10px;
  font: 600 12.5px var(--font-body);
}

.badge-neutral {
  background: var(--surface);
  color: #5C5568;
}

.badge-b2b {
  background: var(--accent-bg);
  color: var(--accent-dark);
  border: 1px solid var(--accent-border);
  padding: 6px 13px;
}

.badge-b2c {
  background: #EAF2FE;
  color: #2158A8;
  border: 1px solid #D6E6FB;
  padding: 6px 13px;
}

.badge-mixed {
  background: #E8F6F3;
  color: #177A6E;
  border: 1px solid #CFEEE7;
  padding: 6px 13px;
}

.copy-btn {
  align-self: flex-start;
  margin-top: 4px;
  font: 600 12px var(--font-body);
  padding: 6px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  transition: border-color .15s, color .15s;
}
.copy-btn:hover { border-color: var(--accent); color: var(--accent); }

@media (max-width: 480px) {
  .card { padding: 24px 20px; }
  .profile-layout { flex-direction: column; }
}
</style>
