<script setup lang="ts">
import { computed, shallowRef, useId, watch } from 'vue'

import NestedFieldList, { type FieldDescriptor } from './NestedFieldList.vue'

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
type StructuredValue = Record<string, JsonValue>

interface Props {
  modelValue: StructuredValue
  fields?: readonly FieldDescriptor[]
  legend?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fields: () => [],
  legend: 'Details',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: StructuredValue]
}>()

const rawInputId = useId()
const rawJson = shallowRef(JSON.stringify(props.modelValue, null, 2))
const rawJsonError = shallowRef<string | null>(null)
const usesRawJson = computed(() => props.fields.length === 0)

watch(
  () => props.modelValue,
  (value) => {
    const serialized = JSON.stringify(value, null, 2)
    if (serialized !== rawJson.value) rawJson.value = serialized
    rawJsonError.value = null
  },
)

function updateRawJson(event: unknown) {
  const input = (event as { currentTarget: { value: string } }).currentTarget
  rawJson.value = input.value
  try {
    const value: unknown = JSON.parse(input.value)
    if (!isStructuredValue(value)) {
      rawJsonError.value = 'Enter a JSON object.'
      return
    }
    rawJsonError.value = null
    emit('update:modelValue', value)
  } catch {
    rawJsonError.value = 'Enter valid JSON.'
  }
}

function isStructuredValue(value: unknown): value is StructuredValue {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
</script>

<template>
  <fieldset class="structured-form" :disabled="disabled">
    <legend class="structured-form__legend">{{ legend }}</legend>
    <div v-if="usesRawJson" class="structured-form__json">
      <label class="structured-form__label" :for="rawInputId">Advanced JSON object input</label>
      <textarea
        :id="rawInputId"
        class="structured-form__control structured-form__control--json"
        :value="rawJson"
        :aria-describedby="rawJsonError ? `${rawInputId}-error` : undefined"
        :aria-invalid="rawJsonError ? 'true' : undefined"
        :disabled="disabled"
        rows="12"
        spellcheck="false"
        @input="updateRawJson"
      />
      <p v-if="rawJsonError" :id="`${rawInputId}-error`" class="structured-form__error" role="alert">
        {{ rawJsonError }}
      </p>
    </div>
    <NestedFieldList
      v-else
      class="structured-form__grid"
      :model-value="modelValue"
      :fields="fields"
      :disabled="disabled"
      @update:model-value="emit('update:modelValue', $event as StructuredValue)"
    />
  </fieldset>
</template>

<style scoped>
.structured-form {
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
}

.structured-form__legend {
  padding: 0 0.375rem;
  font-size: 0.9375rem;
  font-weight: 700;
}

.structured-form__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(14rem, 100%), 1fr));
  gap: 0.875rem;
}

.structured-form__json {
  display: grid;
  gap: 0.5rem;
}

.structured-form__field {
  display: grid;
  align-content: start;
  gap: 0.375rem;
  min-width: 0;
}

.structured-form__label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.structured-form__control {
  width: 100%;
  min-width: 0;
  min-height: 2.625rem;
  box-sizing: border-box;
  padding: 0 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  outline: 0;
  color: inherit;
  background: var(--qava-surface, #ffffff);
  font: inherit;
}

.structured-form__control--json {
  min-height: 14rem;
  padding: 0.75rem;
  resize: vertical;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  line-height: 1.45;
}

.structured-form__error {
  margin: 0;
  color: var(--qava-red, #d94b58);
  font-size: 0.8125rem;
}

.structured-form__control:focus-visible,
.structured-form__check:focus-within {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.structured-form__check {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-height: 2.625rem;
  padding: 0 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface, #ffffff);
}

.structured-form:disabled {
  color: var(--qava-ink-muted, #5f6875);
  background: var(--qava-surface-soft, #f8fafc);
}
</style>