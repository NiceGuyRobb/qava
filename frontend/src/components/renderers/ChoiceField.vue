<script setup lang="ts">
import { useId } from 'vue'

type ChoiceId = string | number | boolean | null

interface Choice {
  id: ChoiceId
  label: string
}

const props = withDefaults(
  defineProps<{
    modelValue: ChoiceId | ChoiceId[]
    label: string
    choices: readonly Choice[]
    multiple?: boolean
    disabled?: boolean
  }>(),
  {
    multiple: false,
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: ChoiceId | ChoiceId[]]
}>()

const groupName = useId()

function isSelected(id: ChoiceId): boolean {
  if (props.multiple) {
    return Array.isArray(props.modelValue) && props.modelValue.some((value) => Object.is(value, id))
  }
  return !Array.isArray(props.modelValue) && Object.is(props.modelValue, id)
}

function selectOne(id: ChoiceId) {
  emit('update:modelValue', id)
}

function toggleChoice(id: ChoiceId, selected: boolean) {
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  const next = selected
    ? [...current.filter((value) => !Object.is(value, id)), id]
    : current.filter((value) => !Object.is(value, id))
  emit('update:modelValue', next)
}

function handleMultipleChange(id: ChoiceId, event: unknown) {
  const input = (event as { target: { checked: boolean } }).target
  toggleChoice(id, input.checked)
}
</script>

<template>
  <fieldset class="choice-field" :disabled="disabled">
    <legend class="choice-field__legend">{{ label }}</legend>
    <div class="choice-field__options">
      <label v-for="choice in choices" :key="`${typeof choice.id}:${String(choice.id)}`" class="choice-field__option">
        <input
          v-if="multiple"
          class="choice-field__input"
          type="checkbox"
          :checked="isSelected(choice.id)"
          @change="handleMultipleChange(choice.id, $event)"
        />
        <input
          v-else
          class="choice-field__input"
          type="radio"
          :name="groupName"
          :checked="isSelected(choice.id)"
          @change="selectOne(choice.id)"
        />
        <span class="choice-field__label">{{ choice.label }}</span>
      </label>
    </div>
  </fieldset>
</template>

<style scoped>
.choice-field {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  color: var(--qava-ink);
}

.choice-field__legend {
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.choice-field__options {
  display: grid;
  gap: 0.5rem;
}

.choice-field__option {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: 0;
  padding: 0.7rem 0.8rem;
  border: 1px solid var(--qava-line);
  border-radius: 8px;
  background: var(--qava-surface);
  cursor: pointer;
}

.choice-field__option:has(.choice-field__input:checked) {
  border-color: var(--qava-focus);
  background: var(--qava-sky-50);
}

.choice-field__input {
  flex: 0 0 auto;
  margin-top: 0.15rem;
  accent-color: var(--qava-focus);
}

.choice-field__input:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--qava-focus) 35%, transparent);
  outline-offset: 3px;
}

.choice-field__label {
  min-width: 0;
  overflow-wrap: anywhere;
}

.choice-field:disabled .choice-field__option {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>