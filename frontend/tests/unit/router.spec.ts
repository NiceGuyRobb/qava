import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'

import { routes } from '@/router'

describe('session routes', () => {
  it('resolves session IDs with respondent metadata', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })

    await router.push('/sessions/session-one')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('session')
    expect(router.currentRoute.value.params.sessionId).toBe('session-one')
    expect(router.currentRoute.value.meta.roles).toEqual(['respondent'])
  })

  it('updates the parameter on same-route navigation', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })

    await router.push('/sessions/session-one')
    await router.push('/sessions/session-two')

    expect(router.currentRoute.value.name).toBe('session')
    expect(router.currentRoute.value.params.sessionId).toBe('session-two')
    expect(router.currentRoute.value.matched[0]?.components?.default).toBe(
      routes[2]?.component,
    )
  })

  it('uses the generic interview view for a meta authoring session', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })

    await router.push('/authoring/sessions/meta-session-one')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('meta-authoring-session')
    expect(router.currentRoute.value.params.sessionId).toBe('meta-session-one')
    expect(router.currentRoute.value.meta.roles).toEqual(['author', 'respondent'])
    expect(router.currentRoute.value.matched[0]?.components?.default).toBe(routes[2]?.component)
  })
})