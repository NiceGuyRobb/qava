<script setup lang="ts">
import { useId } from 'vue'

type DetailValue = string | number | boolean

interface Choice {
  value: string
  label: string
}

interface ProgrammeGroup {
  id: string
  label: string
  items: Choice[]
}

interface ProgrammeDetail {
  key: string
  label: string
  component: 'single_select' | 'short_text' | 'long_text' | 'number' | 'boolean'
  options?: Choice[]
}

interface Selection {
  item_id: string
  status: string
  details?: Record<string, DetailValue>
}

interface ProgrammeValue {
  selections: Selection[]
}

const props = withDefaults(
  defineProps<{
    modelValue: ProgrammeValue
    label: string
    groups: readonly ProgrammeGroup[]
    statuses: readonly Choice[]
    details?: readonly ProgrammeDetail[]
    disabled?: boolean
  }>(),
  { details: () => [], disabled: false },
)

const emit = defineEmits<{
  'update:modelValue': [value: ProgrammeValue]
}>()

const inputPrefix = useId()

function selectionFor(itemId: string): Selection | undefined {
  return props.modelValue.selections.find((selection) => selection.item_id === itemId)
}

function updateStatus(itemId: string, status: string) {
  const existing = selectionFor(itemId)
  const selections = existing
    ? props.modelValue.selections.map((selection) =>
        selection.item_id === itemId ? { ...selection, status } : selection,
      )
    : [...props.modelValue.selections, { item_id: itemId, status }]
  emit('update:modelValue', { selections })
}

function updateDetail(itemId: string, key: string, value: DetailValue | undefined) {
  const existing = selectionFor(itemId)
  if (!existing) return

  const details = { ...existing.details }
  if (value === undefined || value === '') delete details[key]
  else details[key] = value

  const nextSelection = Object.keys(details).length > 0 ? { ...existing, details } : { ...existing }
  if (Object.keys(details).length === 0) delete nextSelection.details
  emit('update:modelValue', {
    selections: props.modelValue.selections.map((selection) =>
      selection.item_id === itemId ? nextSelection : selection,
    ),
  })
}

function detailValue(itemId: string, key: string): DetailValue | undefined {
  return selectionFor(itemId)?.details?.[key]
}

function controlValue(itemId: string, key: string): string | number {
  const value = detailValue(itemId, key)
  return typeof value === 'string' || typeof value === 'number' ? value : ''
}

function handleDetailInput(itemId: string, detail: ProgrammeDetail, event: Event) {
  const input = event.currentTarget as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
  if (detail.component === 'boolean') {
    updateDetail(itemId, detail.key, (input as HTMLInputElement).checked)
    return
  }
  if (detail.component === 'number') {
    const value = input.value === '' ? undefined : Number(input.value)
    updateDetail(itemId, detail.key, Number.isFinite(value) ? value : undefined)
    return
  }
  updateDetail(itemId, detail.key, input.value || undefined)
}
</script>

<template>
  <fieldset class="declared-programme" :disabled="disabled">
    <legend class="declared-programme__legend">{{ label }}</legend>
    <section v-for="group in groups" :key="group.id" class="declared-programme__group">
      <h3 class="declared-programme__group-title">{{ group.label }}</h3>
      <div class="declared-programme__items">
        <article
          v-for="item in group.items"
          :key="item.value"
          class="declared-programme__item"
          :data-programme-item="item.value"
        >
          <label class="declared-programme__item-label" :for="`${inputPrefix}-${item.value}-status`">
            {{ item.label }}
          </label>
          <select
            :id="`${inputPrefix}-${item.value}-status`"
            class="declared-programme__status"
            :value="selectionFor(item.value)?.status ?? ''"
            :disabled="disabled"
            @change="updateStatus(item.value, ($event.target as HTMLSelectElement).value)"
          >
            <option value="" disabled>Select status</option>
            <option v-for="status in statuses" :key="status.value" :value="status.value">
              {{ status.label }}
            </option>
          </select>
          <div v-if="selectionFor(item.value)" class="declared-programme__details">
            <label v-for="detail in details" :key="detail.key" class="declared-programme__detail">
              <span class="declared-programme__detail-label">{{ detail.label }}</span>
              <select
                v-if="detail.component === 'single_select'"
                class="declared-programme__control"
                :value="controlValue(item.value, detail.key)"
                :disabled="disabled"
                @change="handleDetailInput(item.value, detail, $event)"
              >
                <option value="">No preference</option>
                <option v-for="option in detail.options" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <textarea
                v-else-if="detail.component === 'long_text'"
                class="declared-programme__control declared-programme__control--text"
                :value="controlValue(item.value, detail.key)"
                :disabled="disabled"
                rows="3"
                @input="handleDetailInput(item.value, detail, $event)"
              />
              <input
                v-else-if="detail.component === 'short_text' || detail.component === 'number'"
                class="declared-programme__control"
                :type="detail.component === 'number' ? 'number' : 'text'"
                :value="controlValue(item.value, detail.key)"
                :disabled="disabled"
                @input="handleDetailInput(item.value, detail, $event)"
              />
              <input
                v-else
                class="declared-programme__checkbox"
                type="checkbox"
                :checked="detailValue(item.value, detail.key) === true"
                :disabled="disabled"
                @change="handleDetailInput(item.value, detail, $event)"
              />
            </label>
          </div>
        </article>
      </div>
    </section>
  </fieldset>
</template>

<style scoped>
.declared-programme {
  display: grid;
  gap: 1rem;
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
}

.declared-programme__legend {
  padding: 0 0.375rem;
  font-weight: 700;
}

.declared-programme__group {
  display: grid;
  gap: 0.625rem;
}

.declared-programme__group-title {
  margin: 0;
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.875rem;
}

.declared-programme__items {
  display: grid;
  gap: 0.625rem;
}

.declared-programme__item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(9rem, 12rem);
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  background: var(--qava-surface-soft, #f8fafc);
}

.declared-programme__item-label,
.declared-programme__detail {
  min-width: 0;
  overflow-wrap: anywhere;
}

.declared-programme__status,
.declared-programme__control {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 0.55rem 0.65rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  color: inherit;
  background: var(--qava-surface, #ffffff);
  font: inherit;
}

.declared-programme__details {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: 0.625rem;
}

.declared-programme__detail {
  display: grid;
  gap: 0.375rem;
}

.declared-programme__detail-label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.declared-programme__control--text {
  min-height: 5rem;
  resize: vertical;
}

.declared-programme__checkbox {
  width: 1.1rem;
  height: 1.1rem;
  accent-color: var(--qava-focus, #1677c8);
}

.declared-programme__status:focus-visible,
.declared-programme__control:focus-visible,
.declared-programme__checkbox:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--qava-focus, #1677c8) 35%, transparent);
  outline-offset: 2px;
}

@media (max-width: 38rem) {
  .declared-programme__item {
    grid-template-columns: 1fr;
  }
}
</style>