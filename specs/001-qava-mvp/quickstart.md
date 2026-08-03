# Quickstart: Qava MVP

**Feature**: `001-qava-mvp`
**Purpose**: Define the expected clean-checkout developer and acceptance workflow. Commands become executable as their owning delivery slice lands.

## Prerequisites

- Python 3.12
- `uv`
- Node.js 22 LTS and npm
- A Chromium-based browser for Playwright

No external database, cache, identity service, or model provider is required for the deterministic local workflow.

## Initial Setup

```powershell
uv sync --project backend --all-extras
npm ci --prefix frontend
New-Item -ItemType Directory -Force .local | Out-Null
uv run --project backend alembic -c backend/alembic.ini upgrade head
npm --prefix frontend exec playwright install chromium
```

Copy `.env.example` to `.env` only when non-default values are needed. Local defaults use:

- SQLite at `.local/qava.db`;
- generated JSON artifacts at `.local/artifacts/`;
- the explicit development identity provider with author, respondent, and publisher roles;
- assistance disabled or fixture-backed;
- the checked-in `data/` contracts, component catalog, and definitions.

The application MUST create `.local/` at runtime and MUST NOT write production session data under `data/`.

## Validate Contracts and Generate the Client

```powershell
uv run --project backend qava contracts validate --root data
uv run --project backend qava openapi export --output ../specs/001-qava-mvp/contracts/generated.openapi.json
npm --prefix frontend run api:generate
```

Expected result:

- all schemas, catalog entries, definition packs, and examples validate;
- the generated OpenAPI document matches the FastAPI application contract;
- generated TypeScript client output has no uncommitted diff after a second run.

## Run Locally

Terminal 1:

```powershell
uv run --project backend uvicorn qava.main:app --reload --port 8000
```

Terminal 2:

```powershell
npm --prefix frontend run dev -- --port 5173
```

Open `http://localhost:5173`. Vite proxies `/api` and `/openapi.json` to port 8000.

The first usable screen is the Qava workspace, not a marketing page. It shows available published questionnaires or a direct action to author one.

## Seed the Deterministic Demo

```powershell
uv run --project backend qava definitions publish data/definitions/custom-home-intake/v1/definition.json
uv run --project backend qava sessions create --questionnaire custom-home-intake --version 1
```

The second command prints a session ID. Open:

```text
http://localhost:5173/sessions/<session-id>
```

## Verify the Core Loop

1. Confirm the current question appears in the interview pane and the complete canonical output appears in the result pane.
2. Submit a typed answer.
3. Confirm the question transition uses a short directional transform/fade with no overlapping questions.
4. Confirm the revision increments, changed output paths highlight, provenance references the accepted answer, and health/readiness update.
5. Edit the answer and verify dependent applicability, result, provenance, health, readiness, and next interaction recalculate.
6. Reload the browser and verify the exact questionnaire version and latest accepted session state resume.
7. Run with assistance disabled and confirm the interview remains fully operable.

## Verify Responsive and Accessible UX

Desktop target: `1440x900`.

- Interview and full result remain visible in a stable split layout.
- Result supports tree and raw JSON modes, full scrolling, copy/download, revision label, and pointer/provenance selection.
- Health shows completeness, validity, confidence, consistency, specificity, readiness, and evidence-linked attention.
- Publication is visibly separate from answer submission.

Mobile target: `390x844`.

- `Question | Result | Health` control switches views without losing answer state.
- The answer action remains reachable above the safe area.
- Long IDs, prompts, JSON values, and validation messages do not overlap or escape their containers.

Accessibility checks:

- Complete the interview with keyboard only.
- Verify visible focus, programmatic labels, associated errors, and status announcements.
- Test at 200% zoom.
- Enable reduced motion; question replacement must not translate and must complete nearly instantly.
- Status meaning must remain clear without color.

## Preview and Publish

After the session becomes ready:

1. Open publication review.
2. Confirm exact session revision, `json-document` destination, validation result, and external-artifact warning.
3. Preview and confirm no artifact is written.
4. Publish explicitly and record the returned receipt.
5. Repeat with the same idempotency key and confirm the same receipt returns without a second artifact.
6. Delete the session and confirm Qava session-scoped records are removed while the JSON artifact remains.

## Test Commands

Backend fast checks:

```powershell
uv run --project backend ruff check .
uv run --project backend ruff format --check .
uv run --project backend pyright
uv run --project backend pytest tests/unit tests/contract
```

Backend full checks:

```powershell
uv run --project backend pytest
```

Frontend fast checks:

```powershell
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test
```

End-to-end and visual checks, with both servers running:

```powershell
npm --prefix frontend run test:e2e
```

Performance acceptance:

```powershell
uv run --project backend python tests/performance/run_session_load.py --sessions 100
```

The performance report passes only when at least 95% of accepted answers/edits complete within 1 second, all complete within 3 seconds, and no stale write overwrites newer state.

## Full Quality Gate

```powershell
uv run --project backend qava contracts validate --root data
uv run --project backend ruff check .
uv run --project backend ruff format --check .
uv run --project backend pyright
uv run --project backend pytest
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test
npm --prefix frontend run test:e2e
uv run --project backend python tests/performance/run_session_load.py --sessions 100
```

## Troubleshooting Boundaries

- A `409` after answer submission means the client used a stale revision. Replace local state with the latest complete session view; never merge client-derived projection state.
- A `422` means the answer, draft, mapping, readiness gate, or publication request failed a declared contract. Display the returned problem and attention items.
- Assistance failure must create fallback audit evidence and continue with deterministic ordering.
- An unknown component must fail explicitly unless the server supplied a declared compatible fallback.
- SQLite write contention is a deployment/configuration defect for this MVP. Keep one backend worker; do not add distributed locking.
