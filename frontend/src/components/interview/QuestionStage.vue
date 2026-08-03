<script setup lang="ts">
import { shallowRef, watch, type DeepReadonly } from 'vue'

import type { components } from '@/api/generated/schema'
import { useQuestionMotion } from '@/composables/useQuestionMotion'

import SemanticRenderer from './SemanticRenderer.vue'

type RuntimeInteraction = components['schemas']['RuntimeInteraction']

const props = defineProps<{
  interaction: DeepReadonly<RuntimeInteraction> | null
  revision: number
  pending?: boolean
  canSkip?: boolean
}>()

const emit = defineEmits<{
  answer: [value: unknown]
  skip: []
}>()

const draftValue = shallowRef<unknown>(null)
const { transitionName, interactionKey } = useQuestionMotion(
  () => props.interaction?.id ?? null,
)

watch(
  () => props.interaction?.id,
  () => {
    draftValue.value = null
  },
)
</script>

<template>
  <section class="question-stage" aria-live="polite" :aria-busy="pending">
    <Transition :name="transitionName" mode="out-in">
      <div v-if="interaction" :key="interactionKey" class="question-stage__content">
        <header class="question-stage__header">
          <span class="question-stage__kind">{{ interaction.kind }}</span>
          <span class="question-stage__requirement">
            {{ interaction.required ? 'Required' : 'Optional' }}
          </span>
        </header>
        <div class="question-stage__prompt">
          <h1>{{ interaction.prompt }}</h1>
          <p>{{ interaction.reason }}</p>
        </div>
        <SemanticRenderer
          :component-spec="interaction.component"
          :answer-schema="interaction.answer_schema"
          :draft-value="draftValue"
          :prompt="interaction.prompt"
          :disabled="pending"
          @update:model-value="draftValue = $event"
          @submit="emit('answer', $event)"
        />
        <button
          v-if="canSkip"
          class="question-stage__skip"
          type="button"
          :disabled="pending"
          @click="emit('skip')"
        >
          Skip for now
        </button>
      </div>
      <div v-else :key="interactionKey" class="question-stage__complete">
        <span>Interview complete</span>
        <h1>The canonical result is ready for review.</h1>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.question-stage {
  min-width: 0;
  padding: clamp(1rem, 3vw, 2.5rem);
}

.question-stage__content,
.question-stage__complete {
  display: grid;
  gap: 1.25rem;
  max-width: 44rem;
  margin-inline: auto;
}

.question-stage__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--qava-ink-muted);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: capitalize;
}

.question-stage__requirement {
  color: var(--qava-focus);
}

.question-stage__prompt h1,
.question-stage__complete h1 {
  margin: 0;
  font-size: 2rem;
  line-height: 1.15;
  letter-spacing: 0;
}

.question-stage__prompt p {
  margin: 0.5rem 0 0;
  color: var(--qava-ink-muted);
}

.question-stage__skip {
  justify-self: start;
  padding: 0.5rem 0;
  border: 0;
  color: var(--qava-ink-muted);
  background: transparent;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.question-forward-enter-active,
.question-forward-leave-active,
.question-backward-enter-active,
.question-backward-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.question-forward-enter-from,
.question-backward-leave-to {
  opacity: 0;
  transform: translateX(12px);
}

.question-forward-leave-to,
.question-backward-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

@media (prefers-reduced-motion: reduce) {
  .question-forward-enter-active,
  .question-forward-leave-active,
  .question-backward-enter-active,
  .question-backward-leave-active {
    transition-duration: 1ms;
  }

  .question-forward-enter-from,
  .question-forward-leave-to,
  .question-backward-enter-from,
  .question-backward-leave-to {
    transform: none;
  }
}
</style>