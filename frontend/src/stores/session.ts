import { defineStore } from 'pinia'
import { readonly, shallowRef } from 'vue'

import type { components } from '@/api/generated/schema'

export type SessionView = components['schemas']['SessionView']

export const useSessionStore = defineStore('session', () => {
  const mutableView = shallowRef<SessionView | null>(null)
  const view = readonly(mutableView)

  function replace(nextView: SessionView): void {
    mutableView.value = nextView
  }

  function clear(): void {
    mutableView.value = null
  }

  return { view, replace, clear }
})
