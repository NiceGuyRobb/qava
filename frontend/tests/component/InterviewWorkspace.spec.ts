import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { computed, shallowRef, type ComputedRef } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import HealthPanel from '@/components/health/HealthPanel.vue'
import QuestionStage from '@/components/interview/QuestionStage.vue'
import SessionRail from '@/components/interview/SessionRail.vue'
import type { SessionView } from '@/stores/session'

const testState = vi.hoisted(() => ({
  view: undefined as ComputedRef<SessionView> | undefined,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { sessionId: 'session-1' } }),
}))

vi.mock('@/composables/useSession', () => ({
  useSession: () => ({
    view: testState.view,
    pending: shallowRef(false),
    error: shallowRef(null),
    answer: vi.fn(),
    skip: vi.fn(),
    navigate: vi.fn(),
  }),
}))

import InterviewView from '@/views/InterviewView.vue'

const interaction: SessionView['current_interaction'] = {
  id: 'choice-1',
  kind: 'question',
  output_need_ids: ['need-style'],
  prompt: 'Choose a style',
  reason: 'Sets the stable style identifier.',
  required: true,
  answer_schema: { type: 'string', enum: ['modern', 'traditional'] },
  component: {
    name: 'single_select',
    version: 1,
    props: {
      options: [
        { value: 'modern', label: 'Modern' },
        { value: 'traditional', label: 'Traditional' },
      ],
    } as never,
  },
}

function sessionView(): SessionView {
  return {
    session: {
      id: 'session-1',
      questionnaire_id: 'custom-home',
      questionnaire_version: 1,
      revision: 3,
      status: 'active',
    },
    progress: { satisfied_required: 1, total_required: 3 },
    current_interaction: interaction,
    result: {
      session_id: 'session-1',
      revision: 3,
      status: 'in_progress',
      data: { style: 'modern' } as never,
      provenance: { '/style': ['choice-1'] },
      unresolved_output_needs: [
        {
          id: 'need-budget',
          target: '/budget',
          label: 'Budget',
          required: true,
          criticality: 'blocking',
          question_id: 'budget-1',
          topic_id: null,
        },
      ],
      issues: [],
    },
    health: {
      revision: 3,
      score: 72,
      readiness: 'not_ready',
      dimensions: {
        completeness: 34,
        validity: 100,
        confidence: 75,
        consistency: 80,
        specificity: 70,
      },
      attention: [],
      calculation_version: 1,
    },
    actions: ['answer', 'skip', 'navigate', 'save_and_exit'],
    changed_paths: ['/style'],
  } as unknown as SessionView
}

describe('interview workspace', () => {
  beforeEach(() => {
    testState.view = computed(() => sessionView())
  })

  it('submits the selected stable machine value from the question stage', async () => {
    const wrapper = mount(QuestionStage, {
      props: { interaction: interaction as never, revision: 3, canSkip: true },
    })

    await wrapper.findAll('input')[1]?.trigger('change')
    await wrapper.get('.semantic-renderer__submit').trigger('click')

    expect(wrapper.emitted('answer')).toEqual([['traditional']])
  })

  it('emits unresolved output-need navigation from the status rail', async () => {
    const view = sessionView()
    const wrapper = mount(SessionRail, {
      props: {
        session: view.session,
        progress: view.progress,
        readiness: view.health.readiness,
        unresolvedNeeds: view.result.unresolved_output_needs,
      },
    })

    await wrapper.get('summary').trigger('click')
    await wrapper.get('.session-rail__needs button').trigger('click')

    expect(wrapper.emitted('navigate')).toEqual([['need-budget']])
  })

  it('renders every explainable health dimension', () => {
    const wrapper = mount(HealthPanel, { props: { health: sessionView().health as never } })

    for (const label of ['completeness', 'validity', 'confidence', 'consistency', 'specificity']) {
      expect(wrapper.text()).toContain(label)
    }
    expect(wrapper.findAll('progress')).toHaveLength(5)
  })

  it('switches mobile panels without unmounting the question draft surface', async () => {
    const wrapper = mount(InterviewView, {
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.find('.interview-view__question').classes()).not.toContain(
      'interview-view__mobile-hidden',
    )
    await wrapper.get('.interview-view__mobile-tabs button:nth-child(2)').trigger('click')

    expect(wrapper.find('.interview-view__question').classes()).toContain(
      'interview-view__mobile-hidden',
    )
    expect(wrapper.findComponent(QuestionStage).exists()).toBe(true)
    expect(wrapper.find('.interview-view__inspector > div').classes()).not.toContain(
      'interview-view__mobile-hidden',
    )
  })
})
