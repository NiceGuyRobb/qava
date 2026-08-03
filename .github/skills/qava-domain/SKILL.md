---
name: qava-domain
description: "Use when working on Qava's output-contract-driven questionnaires, definition packs, component renderers, drafts, published questionnaires, interview sessions, result projection, health, publication, or Qava frontend-to-API behavior. Covers the contract-first lifecycle, ownership boundaries, immutable versions, browser smoke testing, local workflows, and focused validation."
argument-hint: "Describe the Qava behavior, workflow, definition pack, API, or UI slice to change."
---

# Qava Domain

Qava is an output-driven question-and-answer engine. Its central loop is:

```text
typed answer -> declared mapping -> canonical result draft -> health -> next eligible interaction
```

The purpose of a questionnaire is to produce a usable structured output, not merely to collect answers.

## When To Use

Use this skill for work involving:

- output contracts, questions, mappings, presentation metadata, or definition packs;
- questionnaire draft creation, validation, authoring decisions, and publication;
- interview session progression, answers, skips, navigation, result projection, or health;
- bounded assistance, deterministic fallback, output adapters, or publication receipts;
- FastAPI routes or Vue screens that implement those workflows;
- custom-home intake data and other domain packs.

Also load the applicable implementation skill:

- `python-best-practices` and `fastapi-python` for backend Python changes;
- `vue-best-practices` for Vue, Vite, Pinia, or TypeScript changes;
- `qava-cirrus-design` for Qava UI design or visual QA.

## Product Model

Treat this as the authoritative behavior model:

```text
Output contract
  -> draft questionnaire
  -> author review and validation
  -> immutable published questionnaire version
  -> session pinned to that version
  -> typed answer and deterministic recalculation
  -> canonical result draft and explainable health
  -> explicit publication authorization
  -> adapter delivery and durable receipt
```

The bounded agent may propose authoring decisions, rank eligible interactions, or request clarification within published policy. It must not redefine the contract, weaken validation, remap stable identifiers, or publish on its own. Deterministic eligibility and ordering preserve correct behavior when assistance is disabled, unavailable, or invalid.

## Non-Negotiable Invariants

1. The output contract drives the questionnaire. Questions must have a declared purpose and mapping; do not add questionnaire-specific behavior to generic runtime code.
2. A draft is mutable, reviewable, and may have validation issues or pending decisions. A published questionnaire is immutable and versioned.
3. Publish only after required contract targets are mapped and blocking authoring decisions are resolved.
4. A session pins both questionnaire ID and version. Never silently migrate an existing session to a different published version.
5. The server validates typed answers and applies mappings. Clients render server-declared components and must not carry questionnaire-specific business rules.
6. Each accepted session action advances a revision and recalculates the result, health, attention items, and next interaction.
7. A result preview is not an external side effect. Publication requires explicit user authorization, readiness checks, adapter delivery, and an auditable attempt or receipt.
8. Persist runtime state in repositories/database records; do not make `data/examples/` or `data/definitions/` into production session storage.
9. Keep the engine domain-neutral. Custom-home terms belong in a definition pack, never in contracts or engine behavior.

## Find The Owning Layer

Start with the requested behavior, then read the nearest owning implementation and its focused test.

| Requested behavior | Start here | Then verify nearby |
| --- | --- | --- |
| Contract needs, question shape, publication validation | `backend/src/qava/domain/definition.py` | `backend/tests/unit/test_definition.py`, `backend/tests/contract/test_data_contracts.py` |
| Draft lifecycle and immutable publication | `backend/src/qava/application/authoring.py` | `backend/src/qava/api/routers/questionnaires.py`, `backend/tests/integration/test_authoring_workflow.py` |
| Session progression, answers, projection, health | `backend/src/qava/application/` | `backend/src/qava/api/routers/sessions.py`, `backend/tests/integration/test_interview_workflow.py` |
| Persistence, transactions, records | `backend/src/qava/infrastructure/database/` | `backend/tests/integration/test_repository_invariants.py` |
| Definition-pack compilation | `backend/src/qava/infrastructure/contracts/definition_pack.py` | `data/definitions/`, `backend/tests/unit/test_definition_pack.py` |
| HTTP models, identities, and API contract | `backend/src/qava/api/schemas.py` | `backend/src/qava/api/dependencies.py`, `backend/tests/contract/test_openapi.py` |
| Vue interview behavior | `frontend/src/views/`, `frontend/src/composables/useSession.ts` | `frontend/src/api/client.ts`, `frontend/tests/`, `frontend/e2e/tests/` |

Use [README.md](../../../README.md) for product intent and [docs/data-layout.md](../../../docs/data-layout.md) for authoring-data boundaries. Confirm current implementation behavior in source and tests before treating documentation as executable truth.

## Definition Pack Workflow

Use definition packs as declarative authoring source, not runtime storage.

1. Inspect the manifest in `data/definitions/<definition-id>/v<version>/definition.json`.
2. Read the declared output schema, topics, question files, and shared component catalog.
3. Keep IDs stable and unique. A question belongs to exactly one primary topic.
4. Ensure each question has compatible `answer_schema`, presentation/component metadata, and declared mapping target(s).
5. Use normalized applicability conditions: `{ path, operator, value }`. Recalculate applicability after accepted answers.
6. Keep generated clarifications and trade-offs session-scoped. Do not write them into published deterministic question files.
7. Validate through the existing loader/compiler before proposing a publication flow.

For the custom-home source pack, begin at `data/definitions/custom-home-intake/v1/definition.json`. The files under `data/examples/custom-home-intake/` demonstrate runtime outcomes only; they are not authoring payloads.

## Authoring And Publication Workflow

1. Create or load a draft.
2. Compile its contract and questions to derive output needs and validation issues.
3. Resolve blocking authoring decisions by confirming, overriding, or rejecting them.
4. Validate that every required output need has at least one mapping target.
5. Publish explicitly. The service assigns the next version and stores an immutable `PublishedQuestionnaireRecord`.
6. Use the returned questionnaire ID and version when creating interview sessions.

The local API uses `X-Qava-Identity` containing JSON such as `{"actor_id":"author-1","roles":["author"]}`. Respect role boundaries: authoring endpoints require `author`; session execution requires `respondent`; result publication uses `publisher` where applicable.

## Runtime And UI Workflow

1. Create a session from a published questionnaire ID and version.
2. Retrieve the session view. It is the complete rendering contract: current interaction, component specification, progress, result, health, actions, and changed paths.
3. Submit an answer, skip, or navigation request with the expected revision.
4. Render the returned session view; do not reconstruct result, health, eligibility, or revision logic in the client.
5. Handle `409` as a stale revision: reload the session view before the user continues.
6. Open real interview URLs at `/sessions/{sessionId}`. The root `/sessions` route is only a placeholder shell.

For a local UI run, start the backend from the repository root:

```powershell
uv run --project backend uvicorn qava.main:app --host 127.0.0.1 --port 8000
```

Then start the frontend in a second terminal:

```powershell
Set-Location frontend
npm run dev
```

See [docs/manual-smoke-test.md](../../../docs/manual-smoke-test.md) for the complete manual session flow.

## Definition-Pack Browser Smoke Workflow

Use the compiler-backed browser smoke test after changing a checked-in definition pack, its
compiler, component catalog, or a generic renderer. It is the default regression check for
"publish a fresh version and click through the generated UI" failures.

```powershell
Set-Location frontend
npm run test:e2e:pack
```

The harness in `frontend/e2e/tests/definition-pack-smoke.spec.ts`:

1. compiles `data/definitions/custom-home-intake/v1/definition.json` through the production
  definition-pack compiler;
2. publishes that exact compiled payload through the standard authoring API under a unique test ID;
3. creates an isolated respondent session for each configured conditional scenario;
4. opens every eligible interaction at its real `/sessions/{sessionId}` browser route;
5. fails on an unsupported renderer state, page error, invalid sample answer, stalled progression,
  or incomplete session;
6. runs the existing desktop, mobile, and reduced-motion Chromium projects.

The two scenarios deliberately cover mutually exclusive applicability branches. When adding or
changing a condition, update the scenario answer override and its excluded-question list so the
combined scenarios render every compiled top-level interaction. Do not assert that one scenario
must show questions from its intentionally ineligible branches.

The harness advances sessions with schema-valid API sample answers. It proves the published
contract can reach a renderable browser stage and complete the runtime loop; it does not replace
targeted UI interaction tests for a new control or a manual usability pass.

For a manual check of a changed checked-in definition, restart the local backend, then run
`docs/publish-new-questionnaire-version.ps1` from the repository root. Open the emitted new
session URL. Existing sessions intentionally remain pinned to their original version and cannot
show the new contract.

## Change And Validation Procedure

1. State one local, falsifiable hypothesis about the behavior and choose the smallest check that can disprove it.
2. Change the owner of the behavior, not a forwarding layer or an individual caller, unless the bug is demonstrably local.
3. Preserve public contracts and immutable-version behavior unless the request explicitly changes them.
4. After the first edit, run the narrowest relevant executable validation before widening scope.
5. Run the appropriate broader check for shared contract, persistence, or UI changes.

Typical focused commands:

```powershell
# Backend unit, contract, or integration slice
uv run --project backend pytest backend/tests/unit/test_definition.py -q
uv run --project backend pytest backend/tests/integration/test_authoring_workflow.py -q
uv run --project backend pytest backend/tests/integration/test_interview_workflow.py -q

# Static analysis and formatting checks
uv run --project backend ruff check backend/src backend/tests
uv run --project backend pyright

# Frontend validation
Set-Location frontend
npm run test:unit
npm run test:e2e -- deterministic-interview.spec.ts
npm run test:e2e:pack
```

Prefer the test closest to the edited behavior. For contract or API-schema changes, also run the relevant contract test and check generated OpenAPI expectations. For a definition-pack change, compile/load the pack and test its authoring or session path; JSON validity alone is insufficient.

Run `npm run test:e2e:pack` before manual browser verification whenever the changed slice can
affect the compiled custom-home pack or a generic renderer. If it fails, fix the reported
compiler/contract/renderer boundary before publishing a local version for manual inspection.

## Completion Criteria

Before declaring Qava work complete, verify that:

- the output contract, mappings, and answer schemas remain coherent;
- no published version or session pinning invariant has been bypassed;
- deterministic behavior remains valid with assistance unavailable;
- result, health, and current interaction refresh from the accepted action;
- publication remains explicit and leaves an auditable record;
- the focused executable check for the changed slice passes;
- UI work has been checked at a real session route, not only the placeholder root route.
- definition-pack, compiler, catalog, or renderer changes pass `npm run test:e2e:pack` before a
  manual fresh-version check;
- a manual new-version check, when required, uses a newly created session and does not treat an
  older version-pinned session as evidence of the changed contract.