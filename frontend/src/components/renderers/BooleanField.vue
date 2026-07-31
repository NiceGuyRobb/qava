<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    modelValue: boolean | null
    label: string
    disabled?: boolean
    trueLabel?: string
    falseLabel?: string
    unansweredLabel?: string
  }>(),
  {
    disabled: false,
    trueLabel: 'Yes',
    falseLabel: 'No',
    unansweredLabel: 'Unanswered',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean | null]
}>()

const groupName = useId()
</script>

<template>
  <fieldset class="boolean-field" :disabled="disabled">
    <legend class="boolean-field__legend">{{ label }}</legend>
    <div class="boolean-field__options">
      <label class="boolean-field__option">
        <input
          class="boolean-field__input"
          type="radio"
          :name="groupName"
          :checked="modelValue === true"
          @change="emit('update:modelValue', true)"
        />
        <span>{{ trueLabel }}</span>
      </label>
      <label class="boolean-field__option">
        <input
          class="boolean-field__input"
          type="radio"
          :name="groupName"
          :checked="modelValue === false"
          @change="emit('update:modelValue', false)"
        />
        <span>{{ falseLabel }}</span>
      </label>
      <label class="boolean-field__option">
        <input
          class="boolean-field__input"
          type="radio"
          :name="groupName"
          :checked="modelValue === null"
          @change="emit('update:modelValue', null)"
        />
        <span>{{ unansweredLabel }}</span>
      </label>
    </div>
  </fieldset>
</template>

<style scoped>
.boolean-field {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  color: var(--qava-ink);
}

.boolean-field__legend {
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.boolean-field__options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.boolean-field__option {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  min-height: 2.5rem;
  padding: 0.35rem 0.8rem;
  border: 1px solid var(--qava-line);
  border-radius: 999px;
  background: var(--qava-surface);
  cursor: pointer;
}

.boolean-field__input {
  accent-color: var(--qava-focus);
}

.boolean-field__input:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--qava-focus) 35%, transparent);
  outline-offset: 3px;
}

.boolean-field:disabled .boolean-field__option {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>