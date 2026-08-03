<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePublication } from '@/composables/usePublication'

const props = defineProps<{
  sessionId: string
  revision: number
}>()

const { pending, error, preview, receipt, loadPreview, publish } = usePublication(props.sessionId)

onMounted(loadPreview)

const isOutcomeUnknown = computed(() => receipt.value?.status === 'outcome_unknown')
const isSucceeded = computed(() => receipt.value?.status === 'succeeded')

async function handlePublish() {
  await publish(props.revision)
}
</script>

<template>
  <section class="publication-review" aria-live="polite">
    <h2 class="publication-review__heading">Publish Result</h2>

    <div v-if="pending" class="publication-review__loading" aria-busy="true">
      Loading…
    </div>

    <div
      v-else-if="error"
      class="publication-review__error"
      role="alert"
    >
      <strong>Error</strong>
      <span>{{ error.message }}</span>
    </div>

    <template v-else-if="preview && !receipt">
      <dl class="publication-review__meta">
        <dt>Adapter</dt>
        <dd>{{ preview.adapter }}</dd>
        <dt>Destination</dt>
        <dd class="publication-review__destination">{{ preview.destination }}</dd>
        <dt>Content hash</dt>
        <dd class="publication-review__hash">{{ preview.content_hash }}</dd>
        <dt>Revision</dt>
        <dd>{{ preview.revision }}</dd>
      </dl>

      <details class="publication-review__document">
        <summary>Preview document</summary>
        <pre class="publication-review__json">{{ JSON.stringify(preview.document, null, 2) }}</pre>
      </details>

      <button
        class="publication-review__publish"
        type="button"
        :disabled="pending"
        @click="handlePublish"
      >
        Publish
      </button>
    </template>

    <div v-else-if="receipt" class="publication-review__result">
      <div
        v-if="isSucceeded"
        class="publication-review__success"
        role="status"
      >
        Published — <code>{{ receipt.publication_id }}</code>
      </div>
      <div
        v-else-if="isOutcomeUnknown"
        class="publication-review__unknown"
        role="alert"
      >
        Outcome uncertain. Publication ID: <code>{{ receipt.publication_id }}</code>. Contact your
        administrator to reconcile.
      </div>
      <div
        v-else
        class="publication-review__failed"
        role="alert"
      >
        Publication failed. Status: {{ receipt.status }}.
      </div>
    </div>
  </section>
</template>

<style scoped>
.publication-review {
  display: grid;
  gap: 1.25rem;
  max-width: 52rem;
  padding: 1.5rem;
}

.publication-review__heading {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--qava-ink, #111317);
}

.publication-review__meta {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.375rem 1rem;
  margin: 0;
  font-size: 0.875rem;
}

.publication-review__meta dt {
  font-weight: 650;
  color: var(--qava-ink-muted, #5f6875);
}

.publication-review__destination,
.publication-review__hash {
  word-break: break-all;
  font-family: monospace;
  font-size: 0.8125rem;
}

.publication-review__document {
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  background: var(--qava-surface-soft, #f8fafc);
}

.publication-review__json {
  margin: 0.625rem 0 0;
  font-size: 0.8125rem;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.publication-review__publish {
  justify-self: start;
  min-height: 2.5rem;
  padding: 0.5rem 1.25rem;
  border: 1px solid var(--qava-ink, #111317);
  border-radius: 999px;
  background: var(--qava-ink, #111317);
  color: var(--qava-surface, #ffffff);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.publication-review__publish:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.publication-review__publish:focus-visible {
  outline: 3px solid rgb(22 119 200 / 0.25);
  outline-offset: 2px;
}

.publication-review__success {
  padding: 0.875rem 1rem;
  border: 1px solid var(--qava-green, #1e8c5e);
  border-radius: 8px;
  background: color-mix(in srgb, var(--qava-green, #1e8c5e) 8%, white);
  color: var(--qava-ink, #111317);
}

.publication-review__unknown,
.publication-review__failed {
  padding: 0.875rem 1rem;
  border: 1px solid var(--qava-red, #d94b58);
  border-radius: 8px;
  background: color-mix(in srgb, var(--qava-red, #d94b58) 8%, white);
  color: var(--qava-ink, #111317);
}

.publication-review__error {
  display: grid;
  gap: 0.25rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--qava-red, #d94b58);
  border-radius: 8px;
  background: color-mix(in srgb, var(--qava-red, #d94b58) 8%, white);
}

.publication-review__loading {
  color: var(--qava-ink-muted, #5f6875);
}
</style>
