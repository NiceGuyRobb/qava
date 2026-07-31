<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'

import { apiClient } from '@/api/client'

const router = useRouter()
const error = shallowRef<Error | null>(null)

onMounted(async () => {
  try {
    const view = await apiClient.createSession({
      questionnaire_id: 'meta-questionnaire',
      questionnaire_version: 1,
    })
    await router.replace({ name: 'meta-authoring-session', params: { sessionId: view.session.id } })
  } catch (cause) {
    error.value = cause instanceof Error ? cause : new Error(String(cause))
  }
})
</script>

<template>
  <main class="meta-authoring-start">
    <p v-if="error" class="meta-authoring-start__error" role="alert">{{ error.message }}</p>
    <p v-else class="meta-authoring-start__loading" role="status">Preparing authoring session...</p>
  </main>
</template>

<style scoped>
.meta-authoring-start {
  display: grid;
  place-items: center;
  min-height: 60vh;
  padding: 1.5rem;
}

.meta-authoring-start__loading {
  color: var(--qava-ink-muted, #5f6875);
}

.meta-authoring-start__error {
  color: var(--qava-red, #d94b58);
}
</style>
