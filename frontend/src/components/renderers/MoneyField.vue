<script setup lang="ts">
interface Props {
  modelValue: number | null
  label?: string
  currency?: string
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  label: 'Amount',
  currency: '',
  step: 0.01,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

function updateValue(event: unknown) {
  const input = (event as { currentTarget: { value: string; valueAsNumber: number } }).currentTarget
  if (input.value === '') {
    emit('update:modelValue', null)
    return
  }

  const value = input.valueAsNumber
  emit('update:modelValue', Number.isFinite(value) ? value : null)
}
</script>

<template>
  <label class="money-field">
    <span class="money-field__label">{{ label }}</span>
    <span class="money-field__control">
      <span v-if="currency" class="money-field__currency" aria-hidden="true">{{ currency }}</span>
      <input
        class="money-field__input"
        type="number"
        inputmode="decimal"
        :value="modelValue ?? ''"
        :min="min"
        :max="max"
        :step="step"
        :disabled="disabled"
        @input="updateValue"
      />
    </span>
  </label>
</template>

<style scoped>
.money-field {
  display: grid;
  gap: 0.5rem;
  color: var(--qava-ink, #111317);
}

.money-field__label {
  font-size: 0.875rem;
  font-weight: 650;
}

.money-field__control {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  min-height: 2.75rem;
  overflow: hidden;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface, #ffffff);
}

.money-field__control:focus-within {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.money-field__currency {
  align-self: stretch;
  display: grid;
  place-items: center;
  min-width: 3.5rem;
  padding: 0 0.75rem;
  border-right: 1px solid var(--qava-line, #dbe3eb);
  color: var(--qava-ink-muted, #5f6875);
  background: var(--qava-surface-soft, #f8fafc);
  font-size: 0.8125rem;
  font-weight: 700;
}

.money-field__input {
  min-width: 0;
  height: 2.75rem;
  padding: 0 0.75rem;
  border: 0;
  outline: 0;
  color: inherit;
  background: transparent;
  font: inherit;
}

.money-field__input:disabled {
  cursor: not-allowed;
  color: var(--qava-ink-muted, #5f6875);
  background: var(--qava-surface-soft, #f8fafc);
}
</style>