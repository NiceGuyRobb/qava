<script setup lang="ts">
import { computed, toRaw } from 'vue'
import type { components } from '../../api/generated/schema'
import { resolveRenderer } from '../renderers/registry'

type GeneratedComponentSpec = components['schemas']['ComponentSpec']
type RuntimeComponentSpec = Omit<GeneratedComponentSpec, 'props'> & {
  props: Record<string, unknown>
}

const props = withDefaults(
  defineProps<{
    componentSpec: RuntimeComponentSpec
    answerSchema: Record<string, unknown>
    draftValue: unknown
    prompt?: string
    label?: string
    disabled?: boolean
  }>(),
  {
    prompt: undefined,
    label: undefined,
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  submit: [value: unknown]
}>()

const accessibleLabel = computed(() => props.label ?? props.prompt ?? 'Answer')
const resolution = computed(() =>
  resolveRenderer(props.componentSpec, props.answerSchema, {
    label: accessibleLabel.value,
    draftValue: props.draftValue,
    disabled: props.disabled,
  }),
)

function submit() {
  emit('submit', toRaw(props.draftValue))
}
</script>

<template>
  <div
    v-if="resolution.supported"
    class="semantic-renderer"
    :data-component="resolution.resolvedName"
    :data-fallback="resolution.usedFallback || undefined"
  >
    <component
      :is="resolution.component"
      v-bind="resolution.props"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <button class="semantic-renderer__submit" type="button" :disabled="disabled" @click="submit">
      Submit answer
    </button>
  </div>
  <div
    v-else
    class="semantic-renderer__unsupported"
    role="alert"
    data-unsupported-component
  >
    <strong>Unsupported answer component</strong>
    <span>{{ resolution.reason }}</span>
  </div>
</template>

<style scoped>
.semantic-renderer {
  display: grid;
  gap: 1rem;
}

.semantic-renderer__submit {
  justify-self: start;
  min-height: 2.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--qava-ink, #111317);
  border-radius: 999px;
  color: var(--qava-surface, #ffffff);
  background: var(--qava-ink, #111317);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.semantic-renderer__submit:focus-visible {
  outline: 3px solid rgb(22 119 200 / 0.25);
  outline-offset: 2px;
}

.semantic-renderer__submit:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.semantic-renderer__unsupported {
  display: grid;
  gap: 0.25rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--qava-red, #d94b58);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: color-mix(in srgb, var(--qava-red, #d94b58) 8%, white);
}

.semantic-renderer__unsupported span {
  color: var(--qava-ink-muted, #5f6875);
}
</style>