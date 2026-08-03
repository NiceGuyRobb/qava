import { shallowRef } from 'vue'

import {
  apiClient,
  type PublicationReceipt,
  type QavaApiClient,
  type ResultPreview,
} from '@/api/client'

export function usePublication(sessionId: string, client: QavaApiClient = apiClient) {
  const pending = shallowRef(false)
  const error = shallowRef<Error | null>(null)
  const preview = shallowRef<ResultPreview | null>(null)
  const receipt = shallowRef<PublicationReceipt | null>(null)

  async function loadPreview(): Promise<ResultPreview> {
    pending.value = true
    error.value = null
    try {
      preview.value = await client.previewResult(sessionId)
      return preview.value
    } catch (cause) {
      error.value = cause instanceof Error ? cause : new Error(String(cause))
      throw cause
    } finally {
      pending.value = false
    }
  }

  async function publish(
    expectedRevision: number,
    idempotencyKey?: string,
  ): Promise<PublicationReceipt> {
    pending.value = true
    error.value = null
    const key = idempotencyKey ?? `${sessionId}:${expectedRevision}:${Date.now()}`
    try {
      receipt.value = await client.publishResult(sessionId, {
        idempotency_key: key,
        expected_revision: expectedRevision,
        adapter: 'json_document',
      })
      return receipt.value
    } catch (cause) {
      error.value = cause instanceof Error ? cause : new Error(String(cause))
      throw cause
    } finally {
      pending.value = false
    }
  }

  async function reconcile(publicationId: string): Promise<PublicationReceipt> {
    pending.value = true
    error.value = null
    try {
      receipt.value = await client.reconcilePublication(sessionId, publicationId)
      return receipt.value
    } catch (cause) {
      error.value = cause instanceof Error ? cause : new Error(String(cause))
      throw cause
    } finally {
      pending.value = false
    }
  }

  return { pending, error, preview, receipt, loadPreview, publish, reconcile }
}
