import { afterEach, describe, expect, it, vi } from 'vitest'

import { QavaApiClient } from '@/api/client'

describe('QavaApiClient', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('forwards a configured trusted identity header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ session: { id: 'session-1' } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const identity = JSON.stringify({ actor_id: 'respondent-1', roles: ['respondent'] })
    const client = new QavaApiClient({
      headers: { 'X-Qava-Identity': identity },
    })

    await client.getSession('session-1')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/sessions/session-1',
      expect.objectContaining({
        headers: expect.objectContaining({ 'X-Qava-Identity': identity }),
      }),
    )
  })
})