<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { useRoute } from 'vue-router'

import HealthPanel from '@/components/health/HealthPanel.vue'
import QuestionStage from '@/components/interview/QuestionStage.vue'
import SessionRail from '@/components/interview/SessionRail.vue'
import ResultWorkspace from '@/components/result/ResultWorkspace.vue'
import { useSession } from '@/composables/useSession'

type MobilePanel = 'question' | 'result' | 'health'

const route = useRoute()
const sessionId = computed(() => String(route.params.sessionId ?? ''))
const { view, pending, error, answer, skip, navigate } = useSession(sessionId)
const mobilePanel = shallowRef<MobilePanel>('question')

const resultData = computed(() => (view.value?.result.data ?? {}) as Record<string, unknown>)
const provenance = computed(
  () => (view.value?.result.provenance ?? {}) as Record<string, readonly string[]>,
)

function submitAnswer(value: unknown) {
  void answer(value).catch(() => undefined)
}

function skipInteraction() {
  void skip().catch(() => undefined)
}

function navigateToNeed(outputNeedId: string) {
  void navigate({ output_need_id: outputNeedId }).catch(() => undefined)
}
</script>

<template>
  <div class="interview-view">
    <div v-if="!view && pending" class="interview-view__state" role="status">
      Loading interview…
    </div>
    <div v-else-if="!view && error" class="interview-view__state interview-view__state--error" role="alert">
      <strong>Could not load this interview.</strong>
      <span>{{ error.message }}</span>
    </div>
    <template v-else-if="view">
      <SessionRail
        :session="view.session"
        :progress="view.progress"
        :readiness="view.health.readiness"
        :unresolved-needs="view.result.unresolved_output_needs"
        :pending="pending"
        @navigate="navigateToNeed"
      />

      <nav class="interview-view__mobile-tabs" aria-label="Interview view">
        <button
          v-for="panel in (['question', 'result', 'health'] as const)"
          :key="panel"
          type="button"
          :aria-pressed="mobilePanel === panel"
          @click="mobilePanel = panel"
        >
          {{ panel }}
        </button>
      </nav>

      <main class="interview-view__workspace">
        <div
          class="interview-view__question"
          :class="{ 'interview-view__mobile-hidden': mobilePanel !== 'question' }"
        >
          <p v-if="error" class="interview-view__mutation-error" role="alert">{{ error.message }}</p>
          <QuestionStage
            :interaction="view.current_interaction"
            :revision="view.session.revision"
            :pending="pending"
            :can-skip="view.actions.includes('skip')"
            @answer="submitAnswer"
            @skip="skipInteraction"
          />
        </div>

        <aside class="interview-view__inspector">
          <div :class="{ 'interview-view__mobile-hidden': mobilePanel !== 'result' }">
            <ResultWorkspace
              :result="resultData"
              :provenance="provenance"
              :changed-paths="view.changed_paths"
              :revision="view.session.revision"
            />
          </div>
          <div :class="{ 'interview-view__mobile-hidden': mobilePanel !== 'health' }">
            <HealthPanel :health="view.health" />
          </div>
        </aside>
      </main>
    </template>
  </div>
</template>

<style scoped>
.interview-view {
  min-height: calc(100dvh - 3.5rem);
}

.interview-view__state {
  display: grid;
  place-content: center;
  min-height: 60vh;
  color: var(--qava-ink-muted);
  text-align: center;
}

.interview-view__state--error,
.interview-view__mutation-error {
  color: var(--qava-red);
}

.interview-view__workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(24rem, 0.85fr);
  min-height: calc(100dvh - 7.25rem);
}

.interview-view__question {
  min-width: 0;
  border-right: 1px solid var(--qava-line);
}

.interview-view__mutation-error {
  margin: 0;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--qava-red);
  background: color-mix(in srgb, var(--qava-red) 8%, white);
}

.interview-view__inspector {
  display: grid;
  align-content: start;
  gap: 0.75rem;
  min-width: 0;
  padding: 0.75rem;
}

.interview-view__mobile-tabs {
  display: none;
}

@media (max-width: 52rem) {
  .interview-view__mobile-tabs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 0.4rem;
    border-bottom: 1px solid var(--qava-line);
    background: var(--qava-surface);
  }

  .interview-view__mobile-tabs button {
    min-height: 2.5rem;
    border: 0;
    border-radius: 999px;
    color: var(--qava-ink-muted);
    background: transparent;
    font: inherit;
    font-weight: 700;
    text-transform: capitalize;
  }

  .interview-view__mobile-tabs button[aria-pressed='true'] {
    color: var(--qava-ink);
    background: var(--qava-sky-100);
  }

  .interview-view__workspace {
    display: block;
    min-height: auto;
  }

  .interview-view__question {
    border-right: 0;
  }

  .interview-view__inspector {
    padding: 0.5rem;
  }

  .interview-view__mobile-hidden {
    display: none;
  }
}
</style>