import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ResultWorkspace from '../../src/components/result/ResultWorkspace.vue'

const result = {
  'site/name~label': 'North ridge',
  details: {
    notes: 'x'.repeat(320),
    options: ['solar', 'rainwater'],
    empty: {},
  },
}

describe('ResultWorkspace', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('selects escaped pointers and shows their provenance', async () => {
    const wrapper = mount(ResultWorkspace, {
      props: {
        result,
        provenance: { '/site~1name~0label': ['answer-site', 'interaction-7'] },
        changedPaths: [],
        revision: 7,
      },
    })

    await wrapper.get('[data-pointer="/site~1name~0label"]').trigger('click')

    expect(wrapper.get('[data-testid="selected-pointer"]').text()).toContain('/site~1name~0label')
    expect(wrapper.get('[data-testid="selected-provenance"]').text()).toContain('answer-site')
    expect(wrapper.get('[data-testid="selected-provenance"]').text()).toContain('interaction-7')
  })

  it('switches modes and renders the complete raw document', async () => {
    const wrapper = mount(ResultWorkspace, {
      props: { result, provenance: {}, changedPaths: [], revision: 7 },
    })

    await wrapper.get('[role="tab"][data-mode="raw"]').trigger('click')

    expect(wrapper.get('[role="tab"][data-mode="raw"]').attributes('aria-selected')).toBe('true')
    const raw = wrapper.get('[data-testid="raw-json"]').text()
    expect(raw).toBe(JSON.stringify(result, null, 2))
    expect(raw).toContain('x'.repeat(320))

    await wrapper.get('[role="tab"][data-mode="tree"]').trigger('click')
    expect(wrapper.get('[role="tab"][data-mode="tree"]').attributes('aria-selected')).toBe('true')
  })

  it('marks changed paths for 650ms when changedPaths changes', async () => {
    vi.useFakeTimers()
    const wrapper = mount(ResultWorkspace, {
      props: { result, provenance: {}, changedPaths: [], revision: 7 },
    })

    await wrapper.setProps({ changedPaths: ['/details/notes'] })
    expect(wrapper.get('[data-pointer="/details/notes"]').attributes('data-changed')).toBe('true')
    expect(wrapper.get('[role="status"]').text()).toContain('1 result path changed')

    await vi.advanceTimersByTimeAsync(650)
    expect(wrapper.get('[data-pointer="/details/notes"]').attributes('data-changed')).toBeUndefined()
    expect(wrapper.get('[role="status"]').text()).toBe('')
  })
})