import { defineStore } from 'pinia'
import { readonly, shallowRef } from 'vue'

export type QavaRole = 'author' | 'respondent' | 'publisher'

export interface Identity {
  actorId: string
  roles: readonly QavaRole[]
}

export const useIdentityStore = defineStore('identity', () => {
  const mutableIdentity = shallowRef<Identity | null>(null)
  const identity = readonly(mutableIdentity)

  function replace(nextIdentity: Identity): void {
    mutableIdentity.value = {
      actorId: nextIdentity.actorId,
      roles: [...new Set(nextIdentity.roles)],
    }
  }

  function clear(): void {
    mutableIdentity.value = null
  }

  return { identity, replace, clear }
})
