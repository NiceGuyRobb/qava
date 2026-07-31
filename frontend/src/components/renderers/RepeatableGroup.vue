<script setup lang="ts">
import { computed, shallowRef, useId, watch } from 'vue'

import NestedFieldList, { type FieldDescriptor } from './NestedFieldList.vue'

type RepeatableItem = Record<string, unknown>

interface Props {
  modelValue: readonly RepeatableItem[]
  fields?: readonly FieldDescriptor[]
  legend?: string
  itemLabel?: string
  addLabel?: string
  minItems?: number
  maxItems?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fields: () => [],
  legend: 'Items',
  itemLabel: 'Item',
  addLabel: 'Add item',
  minItems: 0,
  maxItems: 100,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: RepeatableItem[]]
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

function defaultItem(fields: readonly FieldDescriptor[]): RepeatableItem {
  return Object.fromEntries(
    fields.map((field) => {
      if (field.type === 'boolean') return [field.key, false]
      if (field.type === 'group') return [field.key, defaultItem(field.fields ?? [])]
      if (field.type === 'collection') return [field.key, []]
      return [field.key, null]
    }),
  )
}

function addItem() {
  if (props.disabled || props.modelValue.length >= props.maxItems) return
  emit('update:modelValue', [...props.modelValue, defaultItem(props.fields)])
}

function removeItem(index: number) {
  if (props.disabled || props.modelValue.length <= props.minItems) return
  emit('update:modelValue', props.modelValue.filter((_, itemIndex) => itemIndex !== index))
}

function updateItem(index: number, value: RepeatableItem) {
  emit(
    'update:modelValue',
    props.modelValue.map((item, itemIndex) => (itemIndex === index ? value : { ...item })),
  )
}

function updateRawJson(event: unknown) {
  const input = (event as { currentTarget: { value: string } }).currentTarget
  rawJson.value = input.value
  try {
    const value: unknown = JSON.parse(input.value)
    if (!isRepeatableItems(value)) {
      rawJsonError.value = 'Enter a JSON array of objects.'
      return
    }
    rawJsonError.value = null
    emit('update:modelValue', value)
  } catch {
    rawJsonError.value = 'Enter valid JSON.'
  }
}

function isRepeatableItems(value: unknown): value is RepeatableItem[] {
  return Array.isArray(value) && value.every(isRepeatableItem)
}

function isRepeatableItem(value: unknown): value is RepeatableItem {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
</script>

<template>
  <fieldset class="repeatable-group" :disabled="disabled">
    <legend class="repeatable-group__legend">{{ legend }}</legend>
    <div v-if="usesRawJson" class="repeatable-group__json">
      <label class="repeatable-group__label" :for="rawInputId">JSON array of objects</label>
      <textarea
        :id="rawInputId"
        class="repeatable-group__control repeatable-group__control--json"
        :value="rawJson"
        :aria-describedby="rawJsonError ? `${rawInputId}-error` : undefined"
        :aria-invalid="rawJsonError ? 'true' : undefined"
        :disabled="disabled"
        rows="12"
        spellcheck="false"
        @input="updateRawJson"
      />
      <p v-if="rawJsonError" :id="`${rawInputId}-error`" class="repeatable-group__error" role="alert">
        {{ rawJsonError }}
      </p>
    </div>
    <div v-else class="repeatable-group__items">
      <fieldset
        v-for="(item, index) in modelValue"
        :key="index"
        class="repeatable-group__item"
      >
        <legend class="repeatable-group__item-legend">{{ itemLabel }} {{ index + 1 }}</legend>
        <NestedFieldList
          class="repeatable-group__grid"
          :model-value="item"
          :fields="fields"
          :disabled="disabled"
          @update:model-value="(value) => updateItem(index, value)"
        />
        <button
          class="repeatable-group__remove"
          type="button"
          :disabled="disabled || modelValue.length <= minItems"
          @click="removeItem(index)"
        >
          Remove {{ itemLabel.toLowerCase() }}
        </button>
      </fieldset>
    </div>
    <button
      class="repeatable-group__add"
      type="button"
      :disabled="disabled || modelValue.length >= maxItems"
      @click="addItem"
    >
      {{ addLabel }}
    </button>
  </fieldset>
</template>

<style scoped>
.repeatable-group {
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
}

.repeatable-group__legend,
.repeatable-group__item-legend {
  padding: 0 0.375rem;
  font-weight: 700;
}

.repeatable-group__legend {
  font-size: 0.9375rem;
}

.repeatable-group__item-legend {
  font-size: 0.8125rem;
}

.repeatable-group__items {
  display: grid;
  gap: 0.875rem;
}

.repeatable-group__json {
  display: grid;
  gap: 0.5rem;
}

.repeatable-group__item {
  min-width: 0;
  margin: 0;
  padding: 0.875rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface-soft, #f8fafc);
}

.repeatable-group__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: 0.75rem;
}

.repeatable-group__field {
  display: grid;
  gap: 0.375rem;
  min-width: 0;
}

.repeatable-group__label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.repeatable-group__control,
.repeatable-group__check {
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

.repeatable-group__control {
  padding: 0 0.675rem;
  outline: 0;
}

.repeatable-group__control--json {
  min-height: 14rem;
  padding: 0.75rem;
  resize: vertical;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  line-height: 1.45;
}

.repeatable-group__error {
  margin: 0;
  color: var(--qava-red, #d94b58);
  font-size: 0.8125rem;
}

.repeatable-group__check {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.675rem;
}

.repeatable-group__control:focus-visible,
.repeatable-group__check:focus-within {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.repeatable-group__add,
.repeatable-group__remove {
  min-height: 2.375rem;
  border-radius: 999px;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  cursor: pointer;
}

.repeatable-group__add {
  margin-top: 0.875rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--qava-ink, #111317);
  color: var(--qava-surface, #ffffff);
  background: var(--qava-ink, #111317);
}

.repeatable-group__remove {
  margin-top: 0.75rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  color: var(--qava-red, #d94b58);
  background: var(--qava-surface, #ffffff);
}

.repeatable-group__add:focus-visible,
.repeatable-group__remove:focus-visible {
  outline: 3px solid rgb(22 119 200 / 0.25);
  outline-offset: 2px;
}

.repeatable-group__add:disabled,
.repeatable-group__remove:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>