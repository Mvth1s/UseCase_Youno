<template>
  <div class="search-wrapper">
    <div class="search-pill" :class="{ 'has-error': !!inputError }">
      <input
        :value="modelValue"
        type="text"
        placeholder="stripe.com"
        class="search-input"
        aria-label="URL du site à analyser"
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter="$emit('submit')"
      />
      <button
        class="search-btn"
        :disabled="!modelValue.trim()"
        @click="$emit('submit')"
      >
        Analyser
        <svg width="15" height="15" viewBox="0 0 15 15">
          <path d="M2 7.5H13M13 7.5L8.5 3M13 7.5L8.5 12" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <p v-if="inputError" class="input-error">{{ inputError }}</p>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  inputError: { type: String, default: null },
})
defineEmits(['update:modelValue', 'submit'])
</script>

<style scoped>
.search-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: 540px;
}

.search-pill {
  display: flex;
  align-items: center;
  width: 100%;
  background: var(--bg-card);
  border: 1px solid rgba(30, 20, 50, .10);
  border-radius: 999px;
  padding: 6px 6px 6px 26px;
  box-shadow: 0 1px 3px rgba(20,10,40,.05);
  transition: border-color .2s;
}

.search-pill:focus-within { border-color: var(--accent); }
.search-pill.has-error { border-color: #E3B0B0; }

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font: 500 16px var(--font-body);
  background: transparent;
  padding: 13px 0;
  color: var(--text);
  min-width: 0;
}

.search-input::placeholder { color: var(--text-muted); }

.search-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 14px 24px;
  font: 700 15px var(--font-body);
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background .15s;
}

.search-btn:hover:not(:disabled) { background: #5B4BB8; }
.search-btn:disabled { opacity: .5; cursor: not-allowed; }

.input-error {
  font: 600 13px var(--font-body);
  color: #B54444;
}
</style>
