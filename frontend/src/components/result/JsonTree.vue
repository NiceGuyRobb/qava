<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ name: 'JsonTree' })

interface Props {
  value: unknown
  pointer?: string
  selectedPointer?: string
  changedPaths?: readonly string[]
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  pointer: '',
  selectedPointer: '',
  changedPaths: () => [],
  label: 'Result',
})

const emit = defineEmits<{
  select: [pointer: string]
}>()

const isArray = computed(() => Array.isArray(props.value))
const isObject = computed(
  () => props.value !== null && typeof props.value === 'object' && !isArray.value,
)
const entries = computed<[string, unknown][]>(() => {
  if (isArray.value) return (props.value as unknown[]).map((value, index) => [String(index), value])
  if (isObject.value) return Object.entries(props.value as Record<string, unknown>)
  return []
})
const structureLabel = computed(() => {
  if (isArray.value) return entries.value.length === 0 ? '[]' : `Array(${entries.value.length})`
  if (isObject.value) return entries.value.length === 0 ? '{}' : `Object(${entries.value.length})`
  return ''
})
const primitiveType = computed(() => (props.value === null ? 'null' : typeof props.value))
const primitiveText = computed(() => {
  if (props.value === undefined) return 'undefined'
  if (typeof props.value === 'string') return JSON.stringify(props.value)
  return String(props.value)
})
const isChanged = computed(() => props.changedPaths.includes(props.pointer))
const hasChangedDescendant = computed(() => {
  const prefix = props.pointer === '' ? '/' : `${props.pointer}/`
  return props.changedPaths.some((changedPath) => changedPath.startsWith(prefix))
})

function childPointer(segment: string) {
  const escaped = segment.replace(/~/g, '~0').replace(/\//g, '~1')
  return `${props.pointer}/${escaped}`
}
</script>

<template>
  <div
    class="json-tree__node"
    :class="{
      'json-tree__node--selected': selectedPointer === pointer,
      'json-tree__node--changed': isChanged,
      'json-tree__node--contains-change': !isChanged && hasChangedDescendant,
    }"
  >
    <button
      class="json-tree__row"
      type="button"
      :data-pointer="pointer"
      :data-changed="isChanged ? 'true' : undefined"
      :aria-pressed="selectedPointer === pointer"
      :aria-label="`Select JSON pointer ${pointer || 'root'}`"
      @click="emit('select', pointer)"
    >
      <span class="json-tree__key">{{ label }}</span>
      <span v-if="isObject || isArray" class="json-tree__structure">{{ structureLabel }}</span>
      <span v-else class="json-tree__primitive" :class="`json-tree__primitive--${primitiveType}`">
        {{ primitiveText }}
      </span>
      <span v-if="isChanged" class="json-tree__changed-label">Changed</span>
    </button>

    <div v-if="entries.length > 0" class="json-tree__children">
      <JsonTree
        v-for="([key, childValue], index) in entries"
        :key="childPointer(key)"
        :value="childValue"
        :pointer="childPointer(key)"
        :selected-pointer="selectedPointer"
        :changed-paths="changedPaths"
        :label="isArray ? String(index) : key"
        @select="emit('select', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.json-tree__node {
  min-width: max-content;
  border-left: 2px solid transparent;
}

.json-tree__row {
  display: grid;
  grid-template-columns: minmax(7rem, auto) minmax(10rem, 1fr) auto;
  align-items: start;
  gap: 0.75rem;
  width: 100%;
  min-height: 2rem;
  padding: 0.35rem 0.5rem;
  border: 0;
  border-radius: 4px;
  color: var(--qava-ink, #111317);
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.json-tree__row:hover {
  background: var(--qava-surface-soft, #f8fafc);
}

.json-tree__row:focus-visible {
  outline: 2px solid var(--qava-focus, #1677c8);
  outline-offset: -2px;
}

.json-tree__node--selected > .json-tree__row {
  background: var(--qava-sky-100, #eaf5ff);
}

.json-tree__node--changed > .json-tree__row {
  background: color-mix(in srgb, var(--qava-sky-500, #3998e8) 18%, white);
}

.json-tree__node--contains-change {
  border-left-color: var(--qava-sky-500, #3998e8);
}

.json-tree__key,
.json-tree__structure,
.json-tree__primitive,
.json-tree__changed-label {
  font-family: var(--qava-font-mono, monospace);
  font-size: 0.75rem;
  line-height: 1.4;
  letter-spacing: 0;
}

.json-tree__key {
  overflow-wrap: anywhere;
  color: var(--qava-ink, #111317);
  font-weight: 700;
}

.json-tree__structure {
  color: var(--qava-ink-muted, #5f6875);
}

.json-tree__primitive {
  min-width: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.json-tree__primitive--string {
  color: #17633b;
}

.json-tree__primitive--number,
.json-tree__primitive--bigint {
  color: #8a4b08;
}

.json-tree__primitive--boolean {
  color: var(--qava-focus, #1677c8);
}

.json-tree__primitive--null,
.json-tree__primitive--undefined {
  color: var(--qava-ink-muted, #5f6875);
  font-style: italic;
}

.json-tree__changed-label {
  align-self: center;
  color: var(--qava-focus, #1677c8);
  font-family: var(--qava-font-sans, sans-serif);
  font-weight: 700;
}

.json-tree__children {
  margin-left: 0.75rem;
  padding-left: 0.5rem;
  border-left: 1px solid var(--qava-line, #dbe3eb);
}

@media (max-width: 36rem) {
  .json-tree__row {
    grid-template-columns: minmax(5rem, 8rem) minmax(9rem, 1fr) auto;
    gap: 0.5rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .json-tree__node--changed > .json-tree__row {
    transition: none;
  }
}
</style>