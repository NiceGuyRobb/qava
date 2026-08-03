import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const publicationState = vi.hoisted(() => {
  const stateRef = <Value>(value: Value) => ({ __v_isRef: true, value })
  return {
    pending: stateRef(false),
    error: stateRef<Error | null>(null),
    preview: stateRef<Record<string, unknown> | null>(null),
    receipt: stateRef<Record<string, unknown> | null>(null),
    publish: vi.fn(),
  }
})

vi.mock('@/composables/usePublication', () => ({
  usePublication: () => ({
    ...publicationState,
    loadPreview: vi.fn(),
  }),
}))

import PublicationReview from '@/components/publication/PublicationReview.vue'
import DateTimeField from '@/components/renderers/DateTimeField.vue'
import MoneyField from '@/components/renderers/MoneyField.vue'

describe('publication and typed fields', () => {
  beforeEach(() => {
    publicationState.pending.value = false
    publicationState.error.value = null
    publicationState.receipt.value = null
    publicationState.preview.value = {
      adapter: 'json_document',
      destination: 'qava-store://sessions/session-1/artifact',
      content_hash: 'abc123',
      revision: 3,
      document: { project_name: 'North Star' },
    }
    publicationState.publish.mockReset()
  })

  it('shows the exact preview metadata and publishes the supplied revision', async () => {
    const wrapper = mount(PublicationReview, { props: { sessionId: 'session-1', revision: 3 } })

    expect(wrapper.get('.publication-review__meta').text()).toContain('json_document')
    expect(wrapper.get('.publication-review__meta').text()).toContain('abc123')
    await wrapper.get('button').trigger('click')
    expect(publicationState.publish).toHaveBeenCalledWith(3)
  })

  it('announces a successful receipt as a status', () => {
    publicationState.receipt.value = { status: 'succeeded', publication_id: 'publication-1' }
    const wrapper = mount(PublicationReview, { props: { sessionId: 'session-1', revision: 3 } })

    expect(wrapper.get('[role="status"]').text()).toContain('publication-1')
  })

  it('labels the money input and emits a typed numeric value', async () => {
    const wrapper = mount(MoneyField, {
      props: { modelValue: null, label: 'Budget', currency: 'USD' },
    })

    const input = wrapper.get('input')
    expect((input.element as HTMLInputElement).type).toBe('number')
    expect(wrapper.get('label').text()).toContain('Budget')
    await input.setValue('1250.5')
    expect(wrapper.emitted('update:modelValue')).toEqual([[1250.5]])
  })

  it('associates the date-time label and emits an ISO-compatible local value', async () => {
    const wrapper = mount(DateTimeField, {
      props: { modelValue: null, label: 'Appointment', type: 'datetime-local' },
    })

    const label = wrapper.get('label')
    const input = wrapper.get('input')
    expect(label.attributes('for')).toBe(input.attributes('id'))
    await input.setValue('2026-07-26T09:30')
    expect(wrapper.emitted('update:modelValue')).toEqual([['2026-07-26T09:30']])
  })
})