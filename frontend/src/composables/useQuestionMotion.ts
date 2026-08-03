import { computed, toValue, type MaybeRefOrGetter } from 'vue'

export function useQuestionMotion(
  interactionId: MaybeRefOrGetter<string | null>,
  direction: MaybeRefOrGetter<'forward' | 'backward'> = 'forward',
) {
  const transitionName = computed(() => `question-${toValue(direction)}`)
  const interactionKey = computed(() => toValue(interactionId) ?? 'complete')

  return { direction, transitionName, interactionKey }
}