<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    modelValue: string
    label: string
    disabled?: boolean
    multiline?: boolean
    rows?: number
    placeholder?: string
  }>(),
  {
    disabled: false,
    multiline: false,
    rows: 4,
    placeholder: undefined,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputId = useId()

function updateValue(event: unknown) {
  const input = (event as { target: { value: string } }).target
  emit('update:modelValue', input.value)
}
</script>

<template>
  <div class="text-field">
    <label class="text-field__label" :for="inputId">{{ label }}</label>
    <textarea
      v-if="multiline"
      :id="inputId"
      class="text-field__control text-field__control--multiline"
      :value="modelValue"
      :disabled="disabled"
      :rows="rows"
      :placeholder="placeholder"
      @input="updateValue"
    />
    <input
      v-else
      :id="inputId"
      class="text-field__control"
      type="text"
      :value="modelValue"
      :disabled="disabled"
      :placeholder="placeholder"
      @input="updateValue"
    />
  </div>
</template>

<style scoped>
.text-field {
  display: grid;
  gap: 0.5rem;
  color: var(--qava-ink);
}

.text-field__label {
  font-weight: 700;
}

.text-field__control {
  box-sizing: border-box;
  width: 100%;
  min-height: 2.75rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--qava-line);
  border-radius: 8px;
  background: var(--qava-surface);
  color: var(--qava-ink);
  font: inherit;
}

.text-field__control--multiline {
  resize: vertical;
}

.text-field__control:focus-visible {
  border-color: var(--qava-focus);
  outline: 3px solid color-mix(in srgb, var(--qava-focus) 25%, transparent);
  outline-offset: 1px;
}

.text-field__control:disabled {
  cursor: not-allowed;
  background: var(--qava-surface-soft);
  color: var(--qava-ink-muted);
}
</style>