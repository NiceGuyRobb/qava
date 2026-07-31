<script setup lang="ts">
import { AlertTriangle, CheckCircle2, CircleAlert } from '@lucide/vue'
import type { DeepReadonly } from 'vue'
import type { components } from '@/api/generated/schema'

type Health = components['schemas']['HealthAssessment']

defineProps<{ health: DeepReadonly<Health> }>()

const dimensions = ['completeness', 'validity', 'confidence', 'consistency', 'specificity'] as const
</script>

<template>
  <section class="health-panel" aria-labelledby="health-title">
    <header class="health-panel__header">
      <div>
        <span>Result fitness</span>
        <h2 id="health-title">Health</h2>
      </div>
      <div class="health-panel__readiness" :data-readiness="health.readiness" aria-live="polite">
        <CheckCircle2 v-if="health.readiness === 'ready'" :size="18" aria-hidden="true" />
        <AlertTriangle v-else :size="18" aria-hidden="true" />
        <strong>{{ health.readiness.replace('_', ' ') }}</strong>
        <span>{{ health.score }} / 100</span>
      </div>
    </header>
    <dl class="health-panel__dimensions">
      <div v-for="dimension in dimensions" :key="dimension">
        <dt>{{ dimension }}</dt>
        <dd>{{ health.dimensions[dimension] }}</dd>
        <progress :value="health.dimensions[dimension]" max="100">
          {{ health.dimensions[dimension] }}%
        </progress>
      </div>
    </dl>
    <div v-if="health.attention.length" class="health-panel__attention">
      <h3>Attention</h3>
      <article v-for="item in health.attention" :key="`${item.code}:${item.output_need_id ?? ''}`">
        <CircleAlert :size="17" aria-hidden="true" />
        <div>
          <strong>{{ item.message }}</strong>
          <p>{{ item.recommended_action }}</p>
          <code v-if="item.output_need_id">{{ item.output_need_id }}</code>
        </div>
      </article>
    </div>
    <p v-else class="health-panel__clear">No attention items at this revision.</p>
  </section>
</template>

<style scoped>
.health-panel {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--qava-line);
  border-radius: 8px;
  background: var(--qava-surface);
}

.health-panel__header,
.health-panel__readiness {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.health-panel__header h2,
.health-panel__attention h3 {
  margin: 0;
  font-size: 0.9375rem;
}

.health-panel__header > div > span,
.health-panel__readiness span {
  color: var(--qava-ink-muted);
  font-size: 0.75rem;
}

.health-panel__readiness {
  justify-content: flex-end;
  text-transform: capitalize;
}

.health-panel__readiness[data-readiness='ready'] {
  color: var(--qava-green);
}

.health-panel__dimensions {
  display: grid;
  gap: 0.65rem;
  margin: 0;
}

.health-panel__dimensions > div {
  display: grid;
  grid-template-columns: minmax(7rem, 1fr) auto;
  gap: 0.25rem 0.75rem;
}

.health-panel__dimensions dt {
  color: var(--qava-ink-muted);
  font-size: 0.8125rem;
  text-transform: capitalize;
}

.health-panel__dimensions dd {
  margin: 0;
  font-family: var(--qava-font-mono);
  font-size: 0.75rem;
}

.health-panel__dimensions progress {
  grid-column: 1 / -1;
  width: 100%;
  height: 0.35rem;
  accent-color: var(--qava-sky-500);
}

.health-panel__attention {
  display: grid;
  gap: 0.5rem;
}

.health-panel__attention article {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.6rem;
  padding: 0.65rem;
  border-left: 3px solid var(--qava-orange);
  background: var(--qava-surface-soft);
}

.health-panel__attention p,
.health-panel__clear {
  margin: 0.2rem 0 0;
  color: var(--qava-ink-muted);
  font-size: 0.8125rem;
}
</style>