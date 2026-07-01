<template>
  <div class="error-screen">
    <div class="error-icon" :style="{ background: info.bg }">
      <svg width="24" height="24" viewBox="0 0 24 24">
        <path d="M12 3L22 20H2L12 3Z" fill="none" :stroke="info.iconColor" stroke-width="1.7" stroke-linejoin="round"/>
        <path d="M12 9.5V14" :stroke="info.iconColor" stroke-width="1.7" stroke-linecap="round"/>
        <circle cx="12" cy="17" r="1" :fill="info.iconColor"/>
      </svg>
    </div>
    <h2 class="error-title">{{ info.title }}</h2>
    <p class="error-message">{{ info.message }}</p>
    <button class="retry-btn" @click="$emit('retry')">Réessayer</button>
    <span class="error-code">Code {{ errorInfo?.status ?? '?' }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ errorInfo: { type: Object, default: null } })
defineEmits(['retry'])

const ERROR_MAP = {
  400: {
    title: 'URL invalide',
    message: "Vérifiez que l'adresse est correcte (ex. stripe.com) et réessayez.",
    bg: '#FBF3DE', iconColor: '#A9720B',
  },
  408: {
    title: 'Délai dépassé',
    message: 'La requête a dépassé 60 secondes. Le backend est peut-être en cours de démarrage — réessayez.',
    bg: '#FBF3DE', iconColor: '#A9720B',
  },
  429: {
    title: 'Trop de requêtes',
    message: 'Vous avez dépassé la limite de 10 analyses par minute. Attendez un instant avant de réessayer.',
    bg: '#FBF3DE', iconColor: '#A9720B',
  },
  503: {
    title: 'Site injoignable',
    message: "Nous n'avons pas réussi à joindre ce site. Il est peut-être temporairement indisponible — réessayez dans un instant.",
    bg: '#FBEAEA', iconColor: '#B54444',
  },
  500: {
    title: 'Une erreur est survenue',
    message: "Quelque chose s'est mal passé de notre côté. Réessayez dans quelques instants.",
    bg: '#FBEAEA', iconColor: '#B54444',
  },
}

const DEFAULT = { title: 'Une erreur est survenue', message: '', bg: '#FBEAEA', iconColor: '#B54444' }

const info = computed(() => {
  const status = props.errorInfo?.status
  const base = ERROR_MAP[status] ?? DEFAULT
  return { ...base, message: base.message || (props.errorInfo?.detail ?? DEFAULT.message) }
})
</script>

<style scoped>
.error-screen {
  padding-top: 16vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 22px;
  max-width: 440px;
  margin: 0 auto;
}

.error-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-title { font: 600 24px var(--font-heading); color: var(--text); }

.error-message { font: 500 15px/1.6 var(--font-body); color: var(--text-secondary); }

.retry-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 13px 30px;
  font: 700 14px var(--font-body);
  margin-top: 6px;
  transition: background .15s;
}
.retry-btn:hover { background: #5B4BB8; }

.error-code { font: 600 11.5px var(--font-body); color: #C7C0D4; }
</style>
