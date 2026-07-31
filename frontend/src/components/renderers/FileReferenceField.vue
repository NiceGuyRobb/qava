<script setup lang="ts">
interface FileReference {
  id: string
  name: string
  uri: string
  mediaType?: string
  sizeBytes?: number | null
}

interface Props {
  modelValue: readonly FileReference[]
  legend?: string
  addLabel?: string
  maxItems?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  legend: 'File references',
  addLabel: 'Add file reference',
  maxItems: 20,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: FileReference[]]
}>()

function addReference() {
  if (props.disabled || props.modelValue.length >= props.maxItems) return
  emit('update:modelValue', [
    ...props.modelValue,
    { id: '', name: '', uri: '', mediaType: '', sizeBytes: null },
  ])
}

function removeReference(index: number) {
  if (props.disabled) return
  emit('update:modelValue', props.modelValue.filter((_, itemIndex) => itemIndex !== index))
}

function updateReference(index: number, patch: Partial<FileReference>) {
  emit(
    'update:modelValue',
    props.modelValue.map((reference, itemIndex) =>
      itemIndex === index ? { ...reference, ...patch } : { ...reference },
    ),
  )
}

function updateText(index: number, key: 'id' | 'name' | 'uri' | 'mediaType', event: unknown) {
  const input = (event as { currentTarget: { value: string } }).currentTarget
  updateReference(index, { [key]: input.value })
}

function updateSize(index: number, event: unknown) {
  const input = (event as { currentTarget: { value: string; valueAsNumber: number } }).currentTarget
  const value = input.value === '' ? null : input.valueAsNumber
  updateReference(index, { sizeBytes: value === null || Number.isFinite(value) ? value : null })
}
</script>

<template>
  <fieldset class="file-references" :disabled="disabled">
    <legend class="file-references__legend">{{ legend }}</legend>
    <div class="file-references__items">
      <fieldset
        v-for="(reference, index) in modelValue"
        :key="index"
        class="file-references__item"
      >
        <legend class="file-references__item-legend">Reference {{ index + 1 }}</legend>
        <div class="file-references__grid">
          <label class="file-references__field">
            <span class="file-references__label">Stable ID</span>
            <input
              class="file-references__control"
              type="text"
              :value="reference.id"
              autocomplete="off"
              @input="updateText(index, 'id', $event)"
            />
          </label>
          <label class="file-references__field">
            <span class="file-references__label">Display name</span>
            <input
              class="file-references__control"
              type="text"
              :value="reference.name"
              autocomplete="off"
              @input="updateText(index, 'name', $event)"
            />
          </label>
          <label class="file-references__field file-references__field--wide">
            <span class="file-references__label">Durable URI</span>
            <input
              class="file-references__control"
              type="url"
              :value="reference.uri"
              placeholder="https:// or urn:"
              autocomplete="url"
              @input="updateText(index, 'uri', $event)"
            />
          </label>
          <label class="file-references__field">
            <span class="file-references__label">Media type</span>
            <input
              class="file-references__control"
              type="text"
              :value="reference.mediaType ?? ''"
              placeholder="application/pdf"
              autocomplete="off"
              @input="updateText(index, 'mediaType', $event)"
            />
          </label>
          <label class="file-references__field">
            <span class="file-references__label">Size in bytes</span>
            <input
              class="file-references__control"
              type="number"
              inputmode="numeric"
              min="0"
              step="1"
              :value="reference.sizeBytes ?? ''"
              @input="updateSize(index, $event)"
            />
          </label>
        </div>
        <button class="file-references__remove" type="button" @click="removeReference(index)">
          Remove reference
        </button>
      </fieldset>
    </div>
    <button
      class="file-references__add"
      type="button"
      :disabled="disabled || modelValue.length >= maxItems"
      @click="addReference"
    >
      {{ addLabel }}
    </button>
  </fieldset>
</template>

<style scoped>
.file-references {
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
}

.file-references__legend,
.file-references__item-legend {
  padding: 0 0.375rem;
  font-weight: 700;
}

.file-references__legend {
  font-size: 0.9375rem;
}

.file-references__item-legend {
  font-size: 0.8125rem;
}

.file-references__items {
  display: grid;
  gap: 0.875rem;
}

.file-references__item {
  min-width: 0;
  margin: 0;
  padding: 0.875rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  background: var(--qava-surface-soft, #f8fafc);
}

.file-references__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.file-references__field {
  display: grid;
  gap: 0.375rem;
  min-width: 0;
}

.file-references__field--wide {
  grid-column: 1 / -1;
}

.file-references__label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.file-references__control {
  width: 100%;
  min-width: 0;
  min-height: 2.5rem;
  box-sizing: border-box;
  padding: 0 0.675rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  outline: 0;
  color: inherit;
  background: var(--qava-surface, #ffffff);
  font: inherit;
}

.file-references__control:focus-visible {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.file-references__add,
.file-references__remove {
  min-height: 2.375rem;
  border-radius: 999px;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  cursor: pointer;
}

.file-references__add {
  margin-top: 0.875rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--qava-ink, #111317);
  color: var(--qava-surface, #ffffff);
  background: var(--qava-ink, #111317);
}

.file-references__remove {
  margin-top: 0.75rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  color: var(--qava-red, #d94b58);
  background: var(--qava-surface, #ffffff);
}

.file-references__add:focus-visible,
.file-references__remove:focus-visible {
  outline: 3px solid rgb(22 119 200 / 0.25);
  outline-offset: 2px;
}

.file-references__add:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

@media (max-width: 36rem) {
  .file-references__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .file-references__field--wide {
    grid-column: auto;
  }
}
</style>