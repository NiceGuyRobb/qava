import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import type { SessionView } from '@/stores/session'
import { useSessionStore } from '@/stores/session'

function sessionView(revision: number, interactionId: string | null): SessionView {
  return {
    session: {
      id: 'session-1',
      questionnaire_id: 'custom-home-intake',
      questionnaire_version: 1,
      revision,
      status: interactionId === null ? 'completed' : 'active',
    },
    progress: {
      satisfied_required: revision,
      total_required: 3,
    },
    current_interaction:
      interactionId === null
        ? null
        : {
            id: interactionId,
            kind: 'question',
            output_need_ids: ['need-1'],
            prompt: `Question at revision ${revision}`,
            reason: 'Collect required evidence.',
            required: true,
            answer_schema: { type: 'string' },
            component: { name: 'short_text', version: 1, props: {} },
          },
    result: {
      session_id: 'session-1',
      revision,
      status: interactionId === null ? 'ready' : 'in_progress',
      data: {},
      provenance: {},
      unresolved_output_needs: [],
      issues: [],
    },
    health: {
      revision,
      score: revision * 10,
      readiness: interactionId === null ? 'ready' : 'not_ready',
      dimensions: {
        completeness: revision * 10,
        validity: 100,
        confidence: 100,
        consistency: 100,
        specificity: 100,
      },
      attention: [],
      calculation_version: 1,
    },
    actions: interactionId === null ? ['preview_publication'] : ['answer', 'save_and_exit'],
    changed_paths: interactionId === null ? ['/project/name'] : [],
  }
}

describe('session store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('replaces the complete authoritative session view without retaining prior fields', () => {
    const store = useSessionStore()
    const initial = sessionView(1, 'interaction-1')
    const updated = sessionView(2, null)

    store.replace(initial)
    store.replace(updated)

    expect(store.view).toEqual(updated)
    expect(store.view?.current_interaction).toBeNull()
    expect(store.view?.actions).toEqual(['preview_publication'])
    expect(store.view?.changed_paths).toEqual(['/project/name'])
  })

  it('recovers from a stale mutation by replacing local state with a refreshed server view', () => {
    const store = useSessionStore()
    const stale = sessionView(4, 'interaction-4')
    const refreshed = sessionView(5, 'interaction-5')

    store.replace(stale)
    store.replace(refreshed)

    expect(store.view).toEqual(refreshed)
    expect(store.view?.session.revision).toBe(5)
    expect(store.view?.current_interaction?.id).toBe('interaction-5')
    expect(store.view?.result.revision).toBe(5)
    expect(store.view?.health.revision).toBe(5)
  })
})
