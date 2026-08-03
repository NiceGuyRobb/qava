<script setup lang="ts">
import type { components } from '@/api/generated/schema'

type SessionSummary = components['schemas']['SessionSummary']
type Progress = components['schemas']['Progress']
type OutputNeed = components['schemas']['OutputNeedSummary']

defineProps<{
  session: SessionSummary
  progress: Progress
  readiness: components['schemas']['HealthAssessment']['readiness']
  unresolvedNeeds: readonly OutputNeed[]
  pending?: boolean
}>()

const emit = defineEmits<{
  navigate: [outputNeedId: string]
}>()
</script>

<template>
  <aside class="session-rail" aria-label="Interview status">
    <div class="session-rail__identity">
      <strong>{{ session.questionnaire_id }}</strong>
      <span>v{{ session.questionnaire_version }}</span>
      <code>r{{ session.revision }}</code>
    </div>
    <div class="session-rail__progress">
      <span>Requirements</span>
      <strong>{{ progress.satisfied_required }} / {{ progress.total_required }}</strong>
      <progress :value="progress.satisfied_required" :max="Math.max(progress.total_required, 1)">
        {{ progress.satisfied_required }} of {{ progress.total_required }}
      </progress>
    </div>
    <div class="session-rail__readiness" :data-readiness="readiness">
      <span>Readiness</span>
      <strong>{{ readiness.replace('_', ' ') }}</strong>
    </div>
    <details v-if="unresolvedNeeds.length" class="session-rail__needs">
      <summary>{{ unresolvedNeeds.length }} unresolved</summary>
      <button
        v-for="need in unresolvedNeeds"
        :key="need.id"
        type="button"
        :disabled="pending"
        @click="emit('navigate', need.id)"
      >
        <span>{{ need.label ?? need.target }}</span>
        <code>{{ need.id }}</code>
      </button>
    </details>
  </aside>
</template>

<style scoped>
.session-rail {
  display: grid;
  grid-template-columns: minmax(10rem, 1fr) minmax(12rem, 1fr) auto minmax(8rem, auto);
  align-items: center;
  gap: 1rem;
  min-height: 3.75rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--qava-line);
  background: var(--qava-surface);
}

.session-rail__identity,
.session-rail__progress,
.session-rail__readiness {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.session-rail__identity strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-rail code,
.session-rail__identity span,
.session-rail__progress span,
.session-rail__readiness span {
  color: var(--qava-ink-muted);
  font-size: 0.75rem;
}

.session-rail progress {
  width: min(10rem, 100%);
  height: 0.4rem;
  accent-color: var(--qava-sky-500);
}

.session-rail__readiness strong {
  text-transform: capitalize;
}

.session-rail__readiness[data-readiness='ready'] strong {
  color: var(--qava-green);
}

.session-rail__needs {
  position: relative;
}

.session-rail__needs summary {
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 700;
}

.session-rail__needs[open] {
  align-self: start;
  z-index: 2;
  padding: 0.5rem;
  border: 1px solid var(--qava-line);
  border-radius: 6px;
  background: var(--qava-surface);
  box-shadow: var(--qava-shadow);
}

.session-rail__needs button {
  display: grid;
  width: 100%;
  margin-top: 0.35rem;
  padding: 0.45rem;
  border: 0;
  border-radius: 4px;
  background: var(--qava-surface-soft);
  text-align: left;
  cursor: pointer;
}

@media (max-width: 48rem) {
  .session-rail {
    grid-template-columns: 1fr auto;
  }

  .session-rail__progress,
  .session-rail__needs {
    display: none;
  }
}
</style>