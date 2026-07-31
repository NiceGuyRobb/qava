<script setup lang="ts">
import { useId } from 'vue'

type DateTimeInputType = 'date' | 'time' | 'datetime-local'

withDefaults(
  defineProps<{
    modelValue: string | null
    label: string
    type: DateTimeInputType
    disabled?: boolean
    min?: string
    max?: string
    step?: number | 'any'
  }>(),
  {
    disabled: false,
    min: undefined,
    max: undefined,
    step: 'any',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

const inputId = useId()

function updateValue(event: unknown) {
  const value = (event as { target: { value: string } }).target.value
  emit('update:modelValue', value === '' ? null : value)
}
</script>

<template>
  <div class="date-time-field">
    <label class="date-time-field__label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      class="date-time-field__control"
      :type="type"
      :value="modelValue ?? ''"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      @input="updateValue"
    />
  </div>
</template>

<style scoped>
.date-time-field {
  display: grid;
  gap: 0.5rem;
  color: var(--qava-ink);
}

.date-time-field__label {
  font-weight: 700;
}

.date-time-field__control {
  box-sizing: border-box;
  width: 100%;
  min-height: 2.75rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--qava-line);
  border-radius: 8px;
  background: var(--qava-surface);
  color: var(--qava-ink);
  font: inherit;
  color-scheme: light;
}

.date-time-field__control:focus-visible {
  border-color: var(--qava-focus);
  outline: 3px solid color-mix(in srgb, var(--qava-focus) 25%, transparent);
  outline-offset: 1px;
}

.date-time-field__control:disabled {
  cursor: not-allowed;
  background: var(--qava-surface-soft);
  color: var(--qava-ink-muted);
}
</style>