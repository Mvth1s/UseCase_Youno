<template>
  <header class="header">
    <div class="header-inner">
      <div class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="3" fill="#6D5BD0"/>
          <circle cx="12" cy="12" r="7.5" fill="none" stroke="#6D5BD0" stroke-width="1.4" opacity="0.45"/>
          <circle cx="12" cy="12" r="11" fill="none" stroke="#6D5BD0" stroke-width="1.2" opacity="0.22"/>
        </svg>
        <span class="logo-name">Konsole</span>
      </div>
      <span class="tagline">Intelligence commerciale</span>
    </div>
  </header>
</template>

<script setup>
</script>

<style scoped>
.header {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 26px 48px;
  box-sizing: border-box;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-name {
  font: 700 15px var(--font-body);
  letter-spacing: 0.01em;
  color: var(--text);
}

.tagline {
  font: 600 12px var(--font-body);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
}

@media (max-width: 480px) {
  .header { padding: 20px 20px; }
  .tagline { display: none; }
}
</style>
