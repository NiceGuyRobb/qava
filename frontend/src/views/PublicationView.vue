<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PublicationReview from '@/components/publication/PublicationReview.vue'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const store = useSessionStore()

const sessionId = computed(() => route.params.sessionId as string)
const revision = computed(() => store.view?.session.revision ?? 1)
</script>

<template>
  <main class="publication-view">
    <PublicationReview :session-id="sessionId" :revision="revision" />
  </main>
</template>

<style scoped>
.publication-view {
  padding: 1.5rem;
}
</style>
