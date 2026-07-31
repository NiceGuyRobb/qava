<script setup lang="ts">
import { computed, onBeforeUnmount, shallowRef, watch } from 'vue'
import { Copy, Download } from '@lucide/vue'

import JsonTree from './JsonTree.vue'

interface Props {
  result: Record<string, unknown>
  provenance: Record<string, readonly string[]>
  changedPaths: readonly string[]
  revision: number
}

const props = defineProps<Props>()

type Mode = 'tree' | 'raw'

const mode = shallowRef<Mode>('tree')
const selectedPointer = shallowRef('')
const activeChangedPaths = shallowRef<readonly string[]>([])
const commandStatus = shallowRef('')
const changeStatus = shallowRef('')
let changedTimer: ReturnType<typeof globalThis.setTimeout> | undefined

const rawJson = computed(() => JSON.stringify(props.result, null, 2))
const selectedProvenance = computed(() => props.provenance[selectedPointer.value] ?? [])
const liveStatus = computed(() => commandStatus.value || changeStatus.value)

watch(
  () => props.changedPaths,
  (paths) => {
    globalThis.clearTimeout(changedTimer)
    activeChangedPaths.value = [...paths]
    changeStatus.value = paths.length === 0
      ? ''
      : `${paths.length} result ${paths.length === 1 ? 'path' : 'paths'} changed.`
    if (paths.length > 0) {
      changedTimer = globalThis.setTimeout(() => {
        activeChangedPaths.value = []
        changeStatus.value = ''
      }, 650)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => globalThis.clearTimeout(changedTimer))

function selectMode(nextMode: Mode) {
  mode.value = nextMode
}

function handleTabKey(event: unknown) {
  const keyboardEvent = event as {
    key: string
    preventDefault: () => void
    currentTarget: {
      parentElement: { querySelector: (selector: string) => { focus: () => void } | null } | null
    }
  }
  if (keyboardEvent.key !== 'ArrowLeft' && keyboardEvent.key !== 'ArrowRight') return
  keyboardEvent.preventDefault()
  selectMode(mode.value === 'tree' ? 'raw' : 'tree')
  const nextTab = keyboardEvent.currentTarget.parentElement?.querySelector(`[data-mode="${mode.value}"]`)
  nextTab?.focus()
}

async function copyResult() {
  try {
    await globalThis.navigator.clipboard.writeText(rawJson.value)
    commandStatus.value = `Revision ${props.revision} JSON copied.`
  } catch {
    commandStatus.value = 'Could not copy JSON.'
  }
}

function downloadResult() {
  try {
    const url = globalThis.URL.createObjectURL(
      new globalThis.Blob([rawJson.value], { type: 'application/json' }),
    )
    const link = globalThis.document.createElement('a')
    link.href = url
    link.download = `qava-result-revision-${props.revision}.json`
    link.click()
    globalThis.URL.revokeObjectURL(url)
    commandStatus.value = `Revision ${props.revision} JSON downloaded.`
  } catch {
    commandStatus.value = 'Could not download JSON.'
  }
}
</script>

<template>
  <section class="result-workspace" aria-labelledby="result-workspace-title">
    <header class="result-workspace__header">
      <div class="result-workspace__identity">
        <h2 id="result-workspace-title" class="result-workspace__title">Canonical result</h2>
        <span class="result-workspace__revision">Revision {{ revision }}</span>
      </div>

      <div class="result-workspace__commands" aria-label="Result commands">
        <button class="result-workspace__icon-button" type="button" aria-label="Copy JSON" title="Copy JSON" @click="copyResult">
          <Copy :size="17" aria-hidden="true" />
        </button>
        <button class="result-workspace__icon-button" type="button" aria-label="Download JSON" title="Download JSON" @click="downloadResult">
          <Download :size="17" aria-hidden="true" />
        </button>
      </div>
    </header>

    <div class="result-workspace__mode-row">
      <div class="result-workspace__tabs" role="tablist" aria-label="Result display mode" @keydown="handleTabKey">
        <button
          id="result-tree-tab"
          class="result-workspace__tab"
          type="button"
          role="tab"
          data-mode="tree"
          :aria-selected="mode === 'tree'"
          aria-controls="result-tree-panel"
          :tabindex="mode === 'tree' ? 0 : -1"
          @click="selectMode('tree')"
        >
          Tree
        </button>
        <button
          id="result-raw-tab"
          class="result-workspace__tab"
          type="button"
          role="tab"
          data-mode="raw"
          :aria-selected="mode === 'raw'"
          aria-controls="result-raw-panel"
          :tabindex="mode === 'raw' ? 0 : -1"
          @click="selectMode('raw')"
        >
          Raw
        </button>
      </div>
      <p class="result-workspace__live" role="status" aria-live="polite">{{ liveStatus }}</p>
    </div>

    <div class="result-workspace__viewport">
      <div
        v-if="mode === 'tree'"
        id="result-tree-panel"
        class="result-workspace__panel result-workspace__panel--tree"
        role="tabpanel"
        aria-labelledby="result-tree-tab"
      >
        <JsonTree
          :value="result"
          :selected-pointer="selectedPointer"
          :changed-paths="activeChangedPaths"
          @select="selectedPointer = $event"
        />
      </div>
      <pre
        v-else
        id="result-raw-panel"
        class="result-workspace__panel result-workspace__raw"
        role="tabpanel"
        aria-labelledby="result-raw-tab"
        data-testid="raw-json"
      >{{ rawJson }}</pre>
    </div>

    <footer class="result-workspace__selection">
      <div class="result-workspace__pointer">
        <span class="result-workspace__selection-label">Selected pointer</span>
        <code data-testid="selected-pointer">{{ selectedPointer || '(root)' }}</code>
      </div>
      <div class="result-workspace__provenance" data-testid="selected-provenance">
        <span class="result-workspace__selection-label">Provenance</span>
        <ul v-if="selectedProvenance.length > 0" class="result-workspace__source-list">
          <li v-for="source in selectedProvenance" :key="source">{{ source }}</li>
        </ul>
        <span v-else class="result-workspace__empty-source">No provenance for this pointer</span>
      </div>
    </footer>
  </section>
</template>

<style scoped>
.result-workspace {
  display: grid;
  grid-template-rows: auto auto minmax(18rem, 1fr) auto;
  width: 100%;
  min-width: 0;
  min-height: 32rem;
  max-height: min(46rem, calc(100dvh - 8rem));
  overflow: hidden;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: var(--qava-radius-surface, 8px);
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
  box-shadow: var(--qava-shadow, 0 16px 48px rgb(28 55 82 / 0.1));
}

.result-workspace__header,
.result-workspace__mode-row,
.result-workspace__selection {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
}

.result-workspace__header {
  justify-content: space-between;
  border-bottom: 1px solid var(--qava-line, #dbe3eb);
}

.result-workspace__identity,
.result-workspace__commands,
.result-workspace__tabs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.result-workspace__identity {
  min-width: 0;
}

.result-workspace__title {
  margin: 0;
  font-size: 0.9375rem;
  line-height: 1.25;
  letter-spacing: 0;
}

.result-workspace__revision,
.result-workspace__pointer code,
.result-workspace__source-list {
  font-family: var(--qava-font-mono, monospace);
  font-size: 0.75rem;
  letter-spacing: 0;
}

.result-workspace__revision {
  flex: 0 0 auto;
  color: var(--qava-ink-muted, #5f6875);
}

.result-workspace__icon-button {
  display: inline-grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 50%;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
  cursor: pointer;
}

.result-workspace__icon-button:hover {
  border-color: var(--qava-sky-500, #3998e8);
  background: var(--qava-sky-50, #f5faff);
}

.result-workspace__icon-button:focus-visible,
.result-workspace__tab:focus-visible {
  outline: 2px solid var(--qava-focus, #1677c8);
  outline-offset: 2px;
}

.result-workspace__mode-row {
  justify-content: space-between;
  min-height: 3.375rem;
  box-sizing: border-box;
  background: var(--qava-surface-soft, #f8fafc);
}

.result-workspace__tabs {
  padding: 0.1875rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: var(--qava-radius-control, 999px);
  background: var(--qava-surface, #ffffff);
}

.result-workspace__tab {
  min-width: 4.25rem;
  min-height: 1.875rem;
  padding: 0 0.75rem;
  border: 0;
  border-radius: var(--qava-radius-control, 999px);
  color: var(--qava-ink-muted, #5f6875);
  background: transparent;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0;
  cursor: pointer;
}

.result-workspace__tab[aria-selected='true'] {
  color: var(--qava-ink, #111317);
  background: var(--qava-sky-100, #eaf5ff);
}

.result-workspace__live {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.75rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-workspace__viewport {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  border-block: 1px solid var(--qava-line, #dbe3eb);
  background: var(--qava-surface, #ffffff);
  scrollbar-gutter: stable;
}

.result-workspace__panel {
  min-width: 100%;
  min-height: 100%;
  box-sizing: border-box;
}

.result-workspace__panel--tree {
  padding: 0.625rem;
}

.result-workspace__raw {
  margin: 0;
  padding: 1rem;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
  font-family: var(--qava-font-mono, monospace);
  font-size: 0.75rem;
  line-height: 1.55;
  letter-spacing: 0;
  white-space: pre;
}

.result-workspace__selection {
  align-items: stretch;
  background: var(--qava-surface-soft, #f8fafc);
}

.result-workspace__pointer,
.result-workspace__provenance {
  display: grid;
  align-content: start;
  gap: 0.25rem;
  min-width: 0;
}

.result-workspace__pointer {
  flex: 1 1 42%;
}

.result-workspace__provenance {
  flex: 1 1 58%;
}

.result-workspace__selection-label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.6875rem;
  font-weight: 700;
}

.result-workspace__pointer code,
.result-workspace__empty-source,
.result-workspace__source-list {
  overflow-wrap: anywhere;
}

.result-workspace__source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.result-workspace__empty-source {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.75rem;
}

@media (max-width: 36rem) {
  .result-workspace {
    grid-template-rows: auto auto minmax(16rem, 1fr) auto;
    min-height: 29rem;
    max-height: none;
  }

  .result-workspace__mode-row,
  .result-workspace__selection {
    align-items: stretch;
    flex-direction: column;
  }

  .result-workspace__live {
    min-height: 1rem;
    white-space: normal;
  }
}
</style>