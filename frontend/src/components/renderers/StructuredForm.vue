<script setup lang="ts">
import { computed, shallowRef, useId, watch } from 'vue'

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
type FieldValue = string | number | boolean | null
type StructuredValue = Record<string, JsonValue>

interface SelectOption {
  label: string
  value: string | number | boolean
}

interface BaseFieldDescriptor {
  key: string
  label: string
  required?: boolean
}

interface StringFieldDescriptor extends BaseFieldDescriptor {
  type: 'string'
  placeholder?: string
}

interface NumberFieldDescriptor extends BaseFieldDescriptor {
  type: 'number'
  min?: number
  max?: number
  step?: number
}

interface BooleanFieldDescriptor extends BaseFieldDescriptor {
  type: 'boolean'
}

interface SelectFieldDescriptor extends BaseFieldDescriptor {
  type: 'select'
  options: readonly SelectOption[]
}

type FieldDescriptor =
  | StringFieldDescriptor
  | NumberFieldDescriptor
  | BooleanFieldDescriptor
  | SelectFieldDescriptor

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

function emitField(key: string, value: FieldValue) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function updateString(key: string, event: unknown) {
  const input = (event as { currentTarget: { value: string } }).currentTarget
  emitField(key, input.value)
}

function updateNumber(key: string, event: unknown) {
  const input = (event as { currentTarget: { value: string; valueAsNumber: number } }).currentTarget
  const value = input.value === '' ? null : input.valueAsNumber
  emitField(key, value === null || Number.isFinite(value) ? value : null)
}

function updateBoolean(key: string, event: unknown) {
  const input = (event as { currentTarget: { checked: boolean } }).currentTarget
  emitField(key, input.checked)
}

function updateSelect(field: SelectFieldDescriptor, event: unknown) {
  const select = (event as { currentTarget: { value: string } }).currentTarget
  const index = Number(select.value)
  emitField(field.key, field.options[index]?.value ?? null)
}

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

function selectedOptionIndex(field: SelectFieldDescriptor) {
  const value = props.modelValue[field.key]
  const index = field.options.findIndex((option) => Object.is(option.value, value))
  return index < 0 ? '' : String(index)
}

function isStructuredValue(value: unknown): value is StructuredValue {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
</script>

<template>
  <fieldset class="structured-form" :disabled="disabled">
    <legend class="structured-form__legend">{{ legend }}</legend>
    <div v-if="usesRawJson" class="structured-form__json">
      <label class="structured-form__label" :for="rawInputId">JSON object</label>
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
    <div v-else class="structured-form__grid">
      <label v-for="field in fields" :key="field.key" class="structured-form__field">
        <span class="structured-form__label">{{ field.label }}</span>
        <input
          v-if="field.type === 'string'"
          class="structured-form__control"
          type="text"
          :value="modelValue[field.key] ?? ''"
          :placeholder="field.placeholder"
          :required="field.required"
          @input="updateString(field.key, $event)"
        />
        <input
          v-else-if="field.type === 'number'"
          class="structured-form__control"
          type="number"
          :value="modelValue[field.key] ?? ''"
          :min="field.min"
          :max="field.max"
          :step="field.step ?? 'any'"
          :required="field.required"
          @input="updateNumber(field.key, $event)"
        />
        <span v-else-if="field.type === 'boolean'" class="structured-form__check">
          <input
            type="checkbox"
            :checked="modelValue[field.key] === true"
            @change="updateBoolean(field.key, $event)"
          />
          <span>{{ modelValue[field.key] === true ? 'Yes' : 'No' }}</span>
        </span>
        <select
          v-else
          class="structured-form__control"
          :value="selectedOptionIndex(field)"
          :required="field.required"
          @change="updateSelect(field, $event)"
        >
          <option value="" disabled>Select an option</option>
          <option v-for="(option, index) in field.options" :key="index" :value="index">
            {{ option.label }}
          </option>
        </select>
      </label>
    </div>
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