# Quickstart & Validation: README Gap Closure

Run guide proving each slice end to end. Assumes the existing dev setup (backend via `uv run --project backend uvicorn qava.main:app`, frontend via Vite). Run backend tests with `uv run --project backend pytest` and frontend checks with `npm --prefix frontend test`.

## Prerequisites

- Existing deterministic loop passes: `uv run --project backend pytest` and the frontend unit/component suites are green before starting.
- Use the `custom-home-intake` definition as the base fixture; extend only for new answer shapes.

## Slice 1 — Typed capture completion (US1)

1. Publish a questionnaire whose choices come from the `component_catalog` provider, that includes a nested collection, and that has a money and a date/time question.
2. Start a session and answer each; confirm money renders as `MoneyField`, date/time as `DateTimeField`, and options load at runtime.
3. **Expect**: every stored value is a stable typed value (choice `id`, amount+currency, ISO date); the projection reflects the nested collection as an array of typed objects.
- Contracts: [contracts/api-delta.md](contracts/api-delta.md) (unchanged session endpoints). Model: [data-model.md](data-model.md) DynamicOptionSource, Question presentation change.

## Slice 2 — Explicit publication (US2)

1. Take a session to `ready`.
2. `GET .../result/preview` and confirm no artifact is written.
3. `POST .../publications` with `adapter: json_document` and an `idempotency_key`; confirm a receipt and a stored `PublishedArtifact`.
4. Repeat the same request; confirm the same receipt and **no** second artifact.
5. Publish with a stale `expected_revision`; confirm **409** and no artifact.
- Contracts: preview + publications operations. Model: PublishedArtifact, PublicationRecord.

## Slice 3 — Explainable health (US3)

1. Build sessions that exercise weak evidence, a contradiction between two related values, and a present-but-imprecise value.
2. **Expect**: the matching dimension (confidence / consistency / specificity) changes per the fixed rule set and emits a concrete attention item with a recommended action.
3. Confirm validity optionally surfaces adapter dry-run blocking errors before publish.
- Model: HealthAssessmentRecord dimensions change.

## Slice 4 — Authoring decision workflow (US4)

1. Start a draft that surfaces at least one ambiguous decision (`GET .../questionnaire-drafts/{id}` shows `pending`).
2. Resolve it via `POST .../decisions` with `confirm`, then repeat with `override`.
3. Attempt publish with a `pending` blocking decision; confirm **422**.
4. Submit a bulk edit via `PUT .../raw`; confirm it passes the identical gate.
- Contracts: decisions + raw path. Model: AuthoringDecision.

## Slice 5 — Qava authors Qava (US5)

1. Load the bootstrapped meta-questionnaire (published-questionnaire schema as output contract).
2. Answer it to design a five-question questionnaire.
3. Publish via `adapter: registry`; confirm a new immutable questionnaire version and a `{ id, version }` receipt.
4. Start a session against the new version and complete it.
- **Target**: author → publish → run within ~15 minutes using Qava itself.

## Slice 6 — Assistance seam (US6, stub/mock)

1. Enable fixture assistance; confirm each operation returns its hardcoded proposal, validated before use.
2. Feed a fixture proposal that violates schema/policy; confirm rejection and deterministic fallback.
3. Disable fixtures; confirm every interview and authoring path completes deterministically with unchanged results.
- Model: AssistanceProposal (fixture-backed).

## Acceptance

- All new boundary tests plus the existing contract/integration suites are green.
- SC-001…SC-008 evidence recorded; constitution gates remain PASS.
