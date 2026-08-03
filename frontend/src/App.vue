<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <strong class="app-name">Qava</strong>
      <span class="app-status">Contract-first workspace</span>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  color: var(--qava-ink);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 3.5rem;
  padding: 0 1.25rem;
  border-bottom: 1px solid var(--qava-line);
  background: var(--qava-surface);
}

.app-name {
  font-size: 1rem;
}

.app-status {
  color: var(--qava-ink-muted);
  font-size: 0.8125rem;
}

.app-main {
  min-height: calc(100vh - 3.5rem);
}
</style>