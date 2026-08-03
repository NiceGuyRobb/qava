import type { components } from './generated/schema'

// Map generated schema names to stable client-facing aliases
export type CreateDraftRequest = components['schemas']['CreateDraftRequest']
export type CreateSessionRequest = components['schemas']['CreateSessionRequest']
export type SubmitAnswerRequest = components['schemas']['SubmitAnswerRequest']
export type SkipInteractionRequest = components['schemas']['SkipInteractionRequest']
export type NavigateRequest = components['schemas']['NavigateRequest']
export type SessionView = components['schemas']['SessionView']
export type ResultPreview = components['schemas']['ResultPreview']
export type PublishRequest = components['schemas']['PublishRequest']
export type PublicationReceipt = components['schemas']['PublicationReceipt']
export type PublicationList = components['schemas']['PublicationList']

// Legacy aliases kept for back-compat; callers should migrate to the above
/** @deprecated Use SkipInteractionRequest */
export type SessionMutationRequest = SkipInteractionRequest
/** @deprecated Use NavigateRequest */
export type NavigationRequest = NavigateRequest

// Problem detail shape inlined (not a named schema in the generated contract)
export interface ProblemDetail {
  type: string
  title: string
  detail: string
  status: number
  instance?: string
}

export class ApiProblemError extends Error {
  readonly status: number
  readonly problem?: ProblemDetail

  constructor(status: number, message: string, problem?: ProblemDetail) {
    super(message)
    this.name = 'ApiProblemError'
    this.status = status
    this.problem = problem
  }
}

export interface QavaApiClientOptions {
  baseUrl?: string
  headers?: HeadersInit
}

export class QavaApiClient {
  private readonly baseUrl: string
  private readonly defaultHeaders: HeadersInit

  constructor(options: QavaApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? '/api/v1'
    this.defaultHeaders = options.headers ?? {}
  }

  async createDraft(payload: CreateDraftRequest): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('/questionnaire-drafts', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async publishDraft(
    draftId: string,
    expectedRevision: number,
  ): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(
      `/questionnaire-drafts/${encodeURIComponent(draftId)}/publish`,
      {
        method: 'POST',
        headers: {
          'If-Match': String(expectedRevision),
        },
      },
    )
  }

  async createSession(payload: CreateSessionRequest): Promise<SessionView> {
    return this.request<SessionView>('/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async getSession(sessionId: string): Promise<SessionView> {
    return this.request<SessionView>(`/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'GET',
    })
  }

  async submitAnswer(sessionId: string, payload: SubmitAnswerRequest): Promise<SessionView> {
    return this.request<SessionView>(`/sessions/${encodeURIComponent(sessionId)}/answers`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async skipInteraction(
    sessionId: string,
    payload: SessionMutationRequest,
  ): Promise<SessionView> {
    return this.request<SessionView>(`/sessions/${encodeURIComponent(sessionId)}/skips`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async navigateSession(sessionId: string, payload: NavigationRequest): Promise<SessionView> {
    return this.request<SessionView>(`/sessions/${encodeURIComponent(sessionId)}/navigation`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async previewResult(sessionId: string): Promise<ResultPreview> {
    return this.request<ResultPreview>(
      `/sessions/${encodeURIComponent(sessionId)}/result/preview`,
      { method: 'GET' },
    )
  }

  async publishResult(sessionId: string, payload: PublishRequest): Promise<PublicationReceipt> {
    return this.request<PublicationReceipt>(
      `/sessions/${encodeURIComponent(sessionId)}/publications`,
      { method: 'POST', body: JSON.stringify(payload) },
    )
  }

  async listPublications(sessionId: string): Promise<PublicationList> {
    return this.request<PublicationList>(
      `/sessions/${encodeURIComponent(sessionId)}/publications`,
      { method: 'GET' },
    )
  }

  async reconcilePublication(
    sessionId: string,
    publicationId: string,
  ): Promise<PublicationReceipt> {
    return this.request<PublicationReceipt>(
      `/sessions/${encodeURIComponent(sessionId)}/publications/${encodeURIComponent(publicationId)}/reconcile`,
      { method: 'POST' },
    )
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json, application/problem+json',
        'Content-Type': 'application/json',
        ...this.defaultHeaders,
        ...(init.headers ?? {}),
      },
    })

    if (!response.ok) {
      await this.throwProblem(response)
    }

    const payload = (await response.json()) as T
    return payload
  }

  private async throwProblem(response: Response): Promise<never> {
    const contentType = response.headers.get('content-type') ?? ''

    if (contentType.includes('application/problem+json')) {
      const problem = (await response.json()) as ProblemDetail
      throw new ApiProblemError(response.status, problem.detail ?? problem.title, problem)
    }

    const message = await response.text()
    throw new ApiProblemError(response.status, message || `HTTP ${response.status}`)
  }
}

const configuredIdentity = import.meta.env.VITE_QAVA_IDENTITY as string | undefined
const developmentIdentity = import.meta.env.DEV
  ? JSON.stringify({ actor_id: 'qava-web-developer', roles: ['author', 'respondent', 'publisher'] })
  : undefined
const identity = configuredIdentity ?? developmentIdentity

export const apiClient = new QavaApiClient({
  headers: identity === undefined ? {} : { 'X-Qava-Identity': identity },
})
