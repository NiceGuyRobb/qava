import { expect, test, type APIRequestContext } from '@playwright/test'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const apiBase = 'http://127.0.0.1:8000/api/v1'
const authorHeaders = identityHeader('definition-pack-smoke-author', ['author'])
const respondentHeaders = identityHeader('definition-pack-smoke-respondent', ['respondent'])
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url))

interface DefinitionPack {
  title: string
  description: string | null
  output_contract: Record<string, unknown>
  questions: CompiledQuestion[]
}

interface CompiledQuestion {
  id: string
  presentation: { name: string }
}

interface SessionView {
  session: { id: string; revision: number; status: string }
  current_interaction: RuntimeInteraction | null
}

interface RuntimeInteraction {
  id: string
  prompt: string
  required: boolean
  answer_schema: Record<string, unknown>
  component: { name: string }
}

interface SmokeScenario {
  name: string
  answers: Record<string, unknown>
  excludedQuestionIds: string[]
}

const scenarios: SmokeScenario[] = [
  {
    name: 'owned-land path',
    answers: {
      'home-structure': { basement: 'Developed basement', target_area: { value: 1, unit: 'sq_ft' } },
      'outdoor-seasonality': ['Winter'],
    },
    excludedQuestionIds: ['land-search-priorities'],
  },
  {
    name: 'land-search path',
    answers: {
      'land-status': 'Still searching',
      'home-structure': { basement: 'Developed basement', target_area: { value: 1, unit: 'sq_ft' } },
      'outdoor-seasonality': ['Winter'],
    },
    excludedQuestionIds: ['site-location', 'site-known-constraints'],
  },
]

for (const scenario of scenarios) {
  test(`the checked-in definition pack renders every interaction in the ${scenario.name}`, async ({
    page,
    request,
  }) => {
  const pack = compileDefinitionPack()
  const sessionId = await createDefinitionPackInterview(request, pack)
  const pageErrors: Error[] = []
  page.on('pageerror', (error) => pageErrors.push(error))

  const renderedQuestions = new Set<string>()
  let view = await getSession(request, sessionId)

  for (let step = 0; view.current_interaction; step += 1) {
    expect(step, 'The session should advance through the finite definition pack.').toBeLessThan(
      pack.questions.length,
    )

    const interaction = view.current_interaction
    renderedQuestions.add(interaction.id)

    await page.goto(`/sessions/${sessionId}`)
    await expect(page.getByRole('heading', { name: interaction.prompt })).toBeVisible()
    await expect(page.locator('[data-unsupported-component]'), interaction.component.name).toHaveCount(0)

    view = await answerInteraction(request, sessionId, view, interaction, scenario.answers)
  }

  expect(view.session.status).toBe('completed')
  const expectedQuestions = pack.questions
    .filter((question) => !scenario.excludedQuestionIds.includes(question.id))
    .map((question) => question.id)
  expect(renderedQuestions).toEqual(new Set(expectedQuestions))
  expect(pageErrors).toEqual([])
  })
}

function compileDefinitionPack(): DefinitionPack {
  const compiler = [
    'import json',
    'import sys',
    'from pathlib import Path',
    'from qava.infrastructure.contracts.definition_pack import load_definition_pack',
    'pack = load_definition_pack(Path(sys.argv[1]))',
    'print(json.dumps({',
    "    'title': pack.title,",
    "    'description': pack.description,",
    "    'output_contract': pack.output_contract,",
    "    'questions': pack.questions,",
    '}))',
  ].join('\n')
  const result = spawnSync(
    'uv',
    [
      'run',
      '--project',
      'backend',
      'python',
      '-c',
      compiler,
      'data/definitions/custom-home-intake/v1/definition.json',
    ],
    { cwd: repositoryRoot, encoding: 'utf8' },
  )

  if (result.error) throw result.error
  if (result.status !== 0) throw new Error(result.stderr || 'Definition pack compilation failed.')
  return JSON.parse(result.stdout) as DefinitionPack
}

async function createDefinitionPackInterview(
  request: APIRequestContext,
  pack: DefinitionPack,
): Promise<string> {
  const id = `definition-pack-smoke-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const createDraft = await request.post(`${apiBase}/questionnaire-drafts`, {
    headers: authorHeaders,
    data: { id, title: pack.title, description: pack.description, output_contract: pack.output_contract },
  })
  expect(createDraft.status()).toBe(201)

  const updateDraft = await request.put(`${apiBase}/questionnaire-drafts/${id}/raw`, {
    headers: authorHeaders,
    data: {
      title: pack.title,
      description: pack.description,
      output_contract: pack.output_contract,
      questions: pack.questions,
      decisions: [],
    },
  })
  expect(updateDraft.ok()).toBeTruthy()

  const publish = await request.post(`${apiBase}/questionnaire-drafts/${id}/publish`, {
    headers: authorHeaders,
  })
  expect(publish.status()).toBe(201)
  const published = (await publish.json()) as { questionnaire_id: string; version: number }

  const createSession = await request.post(`${apiBase}/sessions`, {
    headers: respondentHeaders,
    data: { questionnaire_id: published.questionnaire_id, questionnaire_version: published.version },
  })
  expect(createSession.status()).toBe(201)
  const view = (await createSession.json()) as SessionView
  return view.session.id
}

async function answerInteraction(
  request: APIRequestContext,
  sessionId: string,
  view: SessionView,
  interaction: RuntimeInteraction,
  answers: Record<string, unknown>,
): Promise<SessionView> {
  const response = await request.post(`${apiBase}/sessions/${sessionId}/answers`, {
    headers: respondentHeaders,
    data: {
      interaction_id: interaction.id,
      value: answers[interaction.id] ?? sampleAnswer(interaction.answer_schema),
      expected_revision: view.session.revision,
    },
  })
  expect(response.ok(), `Could not answer ${interaction.id} with its declared schema.`).toBeTruthy()
  return (await response.json()) as SessionView
}

function sampleAnswer(schema: Record<string, unknown>): unknown {
  const enumerated = schema.enum
  if (Array.isArray(enumerated) && enumerated.length > 0) return enumerated[0]

  switch (schema.type) {
    case 'array': {
      const count = typeof schema.minItems === 'number' && schema.minItems > 0 ? schema.minItems : 0
      const itemSchema = record(schema.items) ?? {}
      return Array.from({ length: count }, () => sampleAnswer(itemSchema))
    }
    case 'boolean':
      return true
    case 'integer':
      return Math.ceil(typeof schema.minimum === 'number' ? schema.minimum : 1)
    case 'number':
      return typeof schema.minimum === 'number' ? schema.minimum : 1
    case 'object': {
      const properties = record(schema.properties) ?? {}
      const required = Array.isArray(schema.required)
        ? schema.required.filter((key): key is string => typeof key === 'string')
        : []
      return Object.fromEntries(
        required.map((key) => [key, sampleAnswer(record(properties[key]) ?? {})]),
      )
    }
    case 'string':
      if (schema.format === 'date') return '2026-01-15'
      if (schema.format === 'date-time') return '2026-01-15T10:00:00'
      return 'Smoke-test answer'
    default:
      return null
  }
}

async function getSession(request: APIRequestContext, sessionId: string): Promise<SessionView> {
  const response = await request.get(`${apiBase}/sessions/${sessionId}`, { headers: respondentHeaders })
  expect(response.ok()).toBeTruthy()
  return (await response.json()) as SessionView
}

function identityHeader(actorId: string, roles: string[]) {
  return { 'X-Qava-Identity': JSON.stringify({ actor_id: actorId, roles }) }
}

function record(value: unknown): Record<string, unknown> | undefined {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined
}