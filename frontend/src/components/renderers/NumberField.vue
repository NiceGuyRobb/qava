<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    modelValue: number | null
    label: string
    disabled?: boolean
    min?: number
    max?: number
    step?: number | 'any'
    placeholder?: string
  }>(),
  {
    disabled: false,
    min: undefined,
    max: undefined,
    step: 'any',
    placeholder: undefined,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const inputId = useId()

function updateValue(event: unknown) {
  const input = (event as { target: { value: string; valueAsNumber: number } }).target
  emit('update:modelValue', input.value === '' ? null : input.valueAsNumber)
}
</script>

<template>
  <div class="number-field">
    <label class="number-field__label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      class="number-field__control"
      type="number"
      inputmode="decimal"
      :value="modelValue ?? ''"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      :placeholder="placeholder"
      @input="updateValue"
    />
  </div>
</template>

<style scoped>
.number-field {
  display: grid;
  gap: 0.5rem;
  color: var(--qava-ink);
}

.number-field__label {
  font-weight: 700;
}

.number-field__control {
  box-sizing: border-box;
  width: 100%;
  min-height: 2.75rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--qava-line);
  border-radius: 8px;
  background: var(--qava-surface);
  color: var(--qava-ink);
  font: inherit;
  font-variant-numeric: tabular-nums;
}

.number-field__control:focus-visible {
  border-color: var(--qava-focus);
  outline: 3px solid color-mix(in srgb, var(--qava-focus) 25%, transparent);
  outline-offset: 1px;
}

.number-field__control:disabled {
  cursor: not-allowed;
  background: var(--qava-surface-soft);
  color: var(--qava-ink-muted);
}
</style>