import { computed, shallowRef, toValue, watch, type MaybeRefOrGetter } from 'vue'

import {
  ApiProblemError,
  apiClient,
  type NavigationRequest,
  type QavaApiClient,
  type SessionView,
} from '@/api/client'
import { useSessionStore } from '@/stores/session'

type NavigationTarget = { section_id: string } | { output_need_id: string }
type SessionActionState = {
  readonly session: { readonly revision: number }
  readonly current_interaction: { readonly id: string } | null
}

export function useSession(
  sessionId: MaybeRefOrGetter<string>,
  client: QavaApiClient = apiClient,
) {
  const store = useSessionStore()
  const pending = shallowRef(false)
  const error = shallowRef<Error | null>(null)
  const view = computed(() => store.view)

  async function fetchLatest(id: string): Promise<SessionView> {
    const latest = await client.getSession(id)
    store.replace(latest)
    return latest
  }

  async function load(): Promise<SessionView> {
    pending.value = true
    error.value = null
    try {
      return await fetchLatest(toValue(sessionId))
    } catch (cause) {
      error.value = asError(cause)
      throw cause
    } finally {
      pending.value = false
    }
  }

  async function mutate(request: () => Promise<SessionView>): Promise<SessionView> {
    pending.value = true
    error.value = null
    try {
      const updated = await request()
      store.replace(updated)
      return updated
    } catch (cause) {
      if (cause instanceof ApiProblemError && cause.status === 409) {
        await fetchLatest(toValue(sessionId))
      }
      error.value = asError(cause)
      throw cause
    } finally {
      pending.value = false
    }
  }

  function answer(value: unknown): Promise<SessionView> {
    const current = requireInteraction(store.view)
    return mutate(() =>
      client.submitAnswer(toValue(sessionId), {
        interaction_id: current.interactionId,
        expected_revision: current.revision,
        value,
      }),
    )
  }

  function skip(): Promise<SessionView> {
    const current = requireInteraction(store.view)
    return mutate(() =>
      client.skipInteraction(toValue(sessionId), {
        interaction_id: current.interactionId,
        expected_revision: current.revision,
      }),
    )
  }

  function navigate(target: NavigationTarget): Promise<SessionView> {
    const current = requireView(store.view)
    const payload: NavigationRequest = {
      expected_revision: current.session.revision,
      ...target,
    }
    return mutate(() => client.navigateSession(toValue(sessionId), payload))
  }

  watch(
    () => toValue(sessionId),
    (nextSessionId) => {
      if (nextSessionId.length > 0) void load().catch(() => undefined)
    },
    { immediate: true },
  )

  return { view, pending, error, load, answer, skip, navigate }
}

function requireView(view: SessionActionState | null): SessionActionState {
  if (view === null) throw new Error('Session is not loaded.')
  return view
}

function requireInteraction(view: SessionActionState | null): {
  interactionId: string
  revision: number
} {
  const loaded = requireView(view)
  if (loaded.current_interaction === null) throw new Error('Session has no current interaction.')
  return {
    interactionId: loaded.current_interaction.id,
    revision: loaded.session.revision,
  }
}

function asError(cause: unknown): Error {
  return cause instanceof Error ? cause : new Error(String(cause))
}