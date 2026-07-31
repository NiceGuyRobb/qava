<script setup lang="ts">
// Recursively renders a list of field descriptors against a record value. Each
// field resolves its own control; nested objects ('group') and nested
// collections ('collection') recurse through this same component so arbitrarily
// nested repeating groups render without any questionnaire-specific logic.

type Primitive = string | number | boolean | null
type RecordValue = Record<string, unknown>
export type FieldValue = Primitive | RecordValue | RecordValue[]

interface SelectOption {
  label: string
  value: string | number | boolean
}

export interface FieldDescriptor {
  key: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'group' | 'collection'
  options?: readonly SelectOption[]
  fields?: readonly FieldDescriptor[]
  placeholder?: string
  min?: number
  max?: number
  step?: number
  itemLabel?: string
  addLabel?: string
  minItems?: number
  maxItems?: number
}

const props = withDefaults(
  defineProps<{
    modelValue: RecordValue
    fields: readonly FieldDescriptor[]
    disabled?: boolean
  }>(),
  { disabled: false },
)

const emit = defineEmits<{
  'update:modelValue': [value: RecordValue]
}>()

function setField(key: string, value: FieldValue) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function asRecord(value: unknown): RecordValue {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as RecordValue)
    : {}
}

function asRows(value: unknown): RecordValue[] {
  return Array.isArray(value) ? (value as RecordValue[]) : []
}

function defaultRecord(fields: readonly FieldDescriptor[]): RecordValue {
  return Object.fromEntries(
    fields.map((field) => {
      if (field.type === 'boolean') return [field.key, false]
      if (field.type === 'group') return [field.key, defaultRecord(field.fields ?? [])]
      if (field.type === 'collection') return [field.key, []]
      return [field.key, null]
    }),
  )
}

function addRow(field: FieldDescriptor) {
  if (props.disabled) return
  const rows = asRows(props.modelValue[field.key])
  if (rows.length >= (field.maxItems ?? 100)) return
  setField(field.key, [...rows, defaultRecord(field.fields ?? [])])
}

function removeRow(field: FieldDescriptor, index: number) {
  if (props.disabled) return
  const rows = asRows(props.modelValue[field.key])
  if (rows.length <= (field.minItems ?? 0)) return
  setField(
    field.key,
    rows.filter((_, rowIndex) => rowIndex !== index),
  )
}

function updateRow(field: FieldDescriptor, index: number, value: RecordValue) {
  const rows = asRows(props.modelValue[field.key])
  setField(
    field.key,
    rows.map((row, rowIndex) => (rowIndex === index ? value : row)),
  )
}

function updateInput(field: FieldDescriptor, event: unknown) {
  const input = (event as {
    currentTarget: { checked: boolean; value: string; valueAsNumber: number }
  }).currentTarget
  if (field.type === 'boolean') {
    setField(field.key, input.checked)
    return
  }
  if (field.type === 'number') {
    const value = input.value === '' ? null : input.valueAsNumber
    setField(field.key, value === null || Number.isFinite(value) ? value : null)
    return
  }
  setField(field.key, input.value)
}

function updateSelect(field: FieldDescriptor, event: unknown) {
  const select = (event as { currentTarget: { value: string } }).currentTarget
  const optionIndex = Number(select.value)
  setField(field.key, field.options?.[optionIndex]?.value ?? null)
}

function selectedOptionIndex(field: FieldDescriptor) {
  const current = props.modelValue[field.key]
  const index = field.options?.findIndex((option) => Object.is(option.value, current)) ?? -1
  return index < 0 ? '' : String(index)
}

function scalarValue(field: FieldDescriptor): string | number {
  const current = props.modelValue[field.key]
  return typeof current === 'string' || typeof current === 'number' ? current : ''
}
</script>

<template>
  <div class="nested-fields">
    <template v-for="field in fields" :key="field.key">
      <fieldset v-if="field.type === 'group'" class="nested-fields__group">
        <legend class="nested-fields__group-legend">{{ field.label }}</legend>
        <NestedFieldList
          :model-value="asRecord(modelValue[field.key])"
          :fields="field.fields ?? []"
          :disabled="disabled"
          @update:model-value="(value) => setField(field.key, value)"
        />
      </fieldset>

      <fieldset v-else-if="field.type === 'collection'" class="nested-fields__collection">
        <legend class="nested-fields__group-legend">{{ field.label }}</legend>
        <fieldset
          v-for="(row, rowIndex) in asRows(modelValue[field.key])"
          :key="rowIndex"
          class="nested-fields__row"
        >
          <legend class="nested-fields__row-legend">
            {{ field.itemLabel ?? 'Item' }} {{ rowIndex + 1 }}
          </legend>
          <NestedFieldList
            :model-value="row"
            :fields="field.fields ?? []"
            :disabled="disabled"
            @update:model-value="(value) => updateRow(field, rowIndex, value)"
          />
          <button
            class="nested-fields__remove"
            type="button"
            :disabled="disabled || asRows(modelValue[field.key]).length <= (field.minItems ?? 0)"
            @click="removeRow(field, rowIndex)"
          >
            Remove
          </button>
        </fieldset>
        <button
          class="nested-fields__add"
          type="button"
          :disabled="disabled || asRows(modelValue[field.key]).length >= (field.maxItems ?? 100)"
          @click="addRow(field)"
        >
          {{ field.addLabel ?? 'Add item' }}
        </button>
      </fieldset>

      <label v-else class="nested-fields__field">
        <span class="nested-fields__label">{{ field.label }}</span>
        <span v-if="field.type === 'boolean'" class="nested-fields__check">
          <input
            type="checkbox"
            :checked="modelValue[field.key] === true"
            :disabled="disabled"
            @change="updateInput(field, $event)"
          />
          <span>{{ modelValue[field.key] === true ? 'Yes' : 'No' }}</span>
        </span>
        <select
          v-else-if="field.type === 'select'"
          class="nested-fields__control"
          :value="selectedOptionIndex(field)"
          :disabled="disabled"
          @change="updateSelect(field, $event)"
        >
          <option value="" disabled>Select an option</option>
          <option v-for="(option, optionIndex) in field.options ?? []" :key="optionIndex" :value="optionIndex">
            {{ option.label }}
          </option>
        </select>
        <input
          v-else
          class="nested-fields__control"
          :type="field.type === 'number' ? 'number' : 'text'"
          :value="scalarValue(field)"
          :placeholder="field.placeholder"
          :min="field.min"
          :max="field.max"
          :step="field.type === 'number' ? field.step ?? 'any' : undefined"
          :disabled="disabled"
          @input="updateInput(field, $event)"
        />
      </label>
    </template>
  </div>
</template>

<style scoped>
.nested-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: 0.75rem;
  min-width: 0;
}

.nested-fields__group,
.nested-fields__collection {
  grid-column: 1 / -1;
  min-width: 0;
  margin: 0;
  padding: 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface-soft, #f8fafc);
  display: grid;
  gap: 0.625rem;
}

.nested-fields__group-legend {
  padding: 0 0.375rem;
  font-size: 0.8125rem;
  font-weight: 700;
}

.nested-fields__row {
  min-width: 0;
  margin: 0;
  padding: 0.625rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface, #ffffff);
  display: grid;
  gap: 0.5rem;
}

.nested-fields__row-legend {
  padding: 0 0.375rem;
  font-size: 0.75rem;
  font-weight: 650;
  color: var(--qava-ink-muted, #5f6875);
}

.nested-fields__field {
  display: grid;
  gap: 0.375rem;
  min-width: 0;
}

.nested-fields__label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.nested-fields__control,
.nested-fields__check {
  width: 100%;
  min-width: 0;
  min-height: 2.5rem;
  box-sizing: border-box;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  color: inherit;
  background: var(--qava-surface, #ffffff);
  font: inherit;
}

.nested-fields__control {
  padding: 0 0.675rem;
  outline: 0;
}

.nested-fields__check {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.675rem;
}

.nested-fields__control:focus-visible,
.nested-fields__check:focus-within {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.nested-fields__add,
.nested-fields__remove {
  justify-self: start;
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface, #ffffff);
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.nested-fields__add:disabled,
.nested-fields__remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
