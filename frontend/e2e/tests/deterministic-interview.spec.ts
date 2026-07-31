import { expect, test, type APIRequestContext, type Page } from '@playwright/test'

const apiBase = 'http://127.0.0.1:8000/api/v1'
const authorHeaders = identityHeader('e2e-author', ['author'])
const respondentHeaders = identityHeader('e2e-respondent', ['respondent'])

test('respondent answers, sees the canonical result, and resumes the exact revision', async ({
  page,
  request,
}) => {
  const sessionId = await createInterview(request)

  await page.goto(`/sessions/${sessionId}`)
  await expect(page.getByRole('heading', { name: 'What should we call this project?' })).toBeVisible()
  await expect(page.getByText('r1', { exact: true })).toBeVisible()
  await openMobilePanel(page, 'result')
  await expect(page.getByRole('region', { name: 'Canonical result' })).toContainText('{}')

  await openMobilePanel(page, 'question')
  await page.getByLabel('What should we call this project?').fill('North Star House')
  await page.getByRole('button', { name: 'Submit answer' }).click()

  await expect(page.getByText('r2', { exact: true })).toBeVisible()
  await expect(page.locator('.session-rail__progress strong')).toHaveText('1 / 1')
  await openMobilePanel(page, 'health')
  await expect(page.getByRole('region', { name: 'Health' })).toContainText(/ready/i)
  await openMobilePanel(page, 'result')
  await page.getByRole('tab', { name: 'Raw' }).click()
  await expect(page.getByRole('tabpanel', { name: 'Raw' })).toContainText('North Star House')

  await page.reload()

  await expect(page.getByText('r2', { exact: true })).toBeVisible()
  await openMobilePanel(page, 'result')
  await page.getByRole('tab', { name: 'Raw' }).click()
  await expect(page.getByRole('tabpanel', { name: 'Raw' })).toContainText('North Star House')
})

async function openMobilePanel(page: Page, panel: 'question' | 'result' | 'health') {
  const button = page.locator('.interview-view__mobile-tabs').getByRole('button', { name: panel })
  if (await button.isVisible()) await button.click()
}

async function createInterview(request: APIRequestContext): Promise<string> {
  const id = `e2e-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const createDraft = await request.post(`${apiBase}/questionnaire-drafts`, {
    headers: authorHeaders,
    data: {
      id,
      title: 'Deterministic E2E',
      output_contract: {
        type: 'object',
        properties: { project_name: { type: 'string' } },
        required: ['project_name'],
      },
    },
  })
  expect(createDraft.status()).toBe(201)

  const updateDraft = await request.patch(`${apiBase}/questionnaire-drafts/${id}`, {
    headers: authorHeaders,
    data: {
      operations: [
        {
          operation: 'upsert_question',
          question: {
            id: 'project-name',
            prompt: 'What should we call this project?',
            output_need_ids: ['need:project_name'],
            answer_schema: { type: 'string' },
            mapping: { mode: 'direct', target: '/project_name' },
            presentation: { name: 'short_text', version: 1, props: {} },
            required: true,
            order: 1,
          },
        },
      ],
    },
  })
  expect(updateDraft.ok()).toBeTruthy()

  const publish = await request.post(`${apiBase}/questionnaire-drafts/${id}/publish`, {
    headers: authorHeaders,
  })
  expect(publish.status()).toBe(201)

  const createSession = await request.post(`${apiBase}/sessions`, {
    headers: respondentHeaders,
    data: { questionnaire_id: id, questionnaire_version: 1 },
  })
  expect(createSession.status()).toBe(201)
  const view = (await createSession.json()) as { session: { id: string } }
  return view.session.id
}

function identityHeader(actorId: string, roles: string[]) {
  return { 'X-Qava-Identity': JSON.stringify({ actor_id: actorId, roles }) }
}