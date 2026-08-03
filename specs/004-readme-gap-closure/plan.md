# Implementation Plan: README Gap Closure

**Branch**: `004-readme-gap-closure` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-readme-gap-closure/spec.md`

## Summary

Close the highest-value README gaps on top of the working deterministic core, without rewriting it. Five slices ship real behavior (typed-capture completion, explicit publication, rule-based health, the authoring decision workflow, and self-hosted authoring), and one slice reserves the bounded-agent seam as an interface plus hardcoded fixtures. Every addition composes an existing domain seam and preserves the `published questionnaire + session answers -> next interaction + result + health` loop.

## Technical Context

**Language/Version**: Python 3.12 (backend engine + FastAPI); TypeScript 5.x / Vue 3.5 (client)

**Primary Dependencies**: FastAPI, Pydantic v2, `jsonschema`, SQLAlchemy 2 async, `aiosqlite`, Alembic; Vue 3, Vite, Pinia, Vue Router 4 — all already in the workspace; no new runtime dependencies.

**Storage**: Existing SQLite. `publication_attempts` and `assistance_proposals` tables already exist and are reused; a new immutable published-artifact store (table) holds JSON document adapter outputs.

**Testing**: pytest / pytest-asyncio / HTTPX (backend); Vitest / Vue Test Utils / vue-tsc (frontend); Playwright for the self-hosting end-to-end. New behavior gets a paired boundary test; existing contract + integration suites must stay green.

**Target Platform**: Single-tenant container; evergreen browsers. Unchanged from `001`.

**Project Type**: One backend engine/API + one Vue SPA (existing).

**Performance Goals**: Preserve `001` targets (95% of accepted mutations return a full session view < 1s at 100 sessions). No new hot paths beyond one adapter write per explicit publish.

**Constraints**: Reuse existing seams; no bespoke authoring builder; no real AI provider; collection depth 3 / 100 items (existing config); publication is explicit, gated, idempotent.

**Scale/Scope**: Six prioritized slices; JSON document + registry adapters only; one built-in web catalog.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Result | Evidence |
|---|---|---|
| Output contract | PASS | Dynamic options, collections, publication, and the meta output contract all resolve against declared output needs in `domain/definition.py`; no competing source of truth. |
| Simple runtime | PASS | New capabilities are functions/services over the same evaluation seam (`domain/evaluation.py`); no workflow graph or new runtime model. |
| Typed UI | PASS | New controls (money, date/time, dynamic options, nested collections) emit stable typed values through the existing renderer-neutral client; no questionnaire logic added to clients. |
| Bounded AI | PASS | US6 is interface + fixtures only, always validated and behind deterministic fallback; the engine is fully operable with assistance disabled. |
| Continuous projection | PASS | Every new mutation path routes through the single evaluation that recomputes projection, provenance, health, readiness, and next interaction. |
| Explainable health | PASS | Health dimensions move to a fixed, built-in, inspectable rule set with evidence-linked attention items; score never publishes alone. |
| Stable publication | PASS | Publication is explicit, gated, idempotent, and receipted; published questionnaires and the meta-questionnaire remain immutable and versioned. |

All gates PASS pre-research. Re-check after Phase 1 design: **PASS**. No Complexity Tracking entry required.

## Project Structure

### Documentation (this feature)

```text
specs/004-readme-gap-closure/
├── plan.md          # This file
├── research.md      # Phase 0 decisions
├── data-model.md    # Phase 1 entities (new/changed only)
├── quickstart.md    # Phase 1 validation scenarios
├── contracts/
│   └── api-delta.md # New/changed endpoints only
└── tasks.md         # /speckit.tasks output (not created here)
```

### Source Code — delta on the existing tree

Only additions and touched files are listed; everything else is unchanged.

```text
backend/src/qava/
├── application/
│   ├── options.py        # NEW: resolve named runtime option providers (US1)
│   ├── publishing.py     # NEW: preview + explicit idempotent publication (US2)
│   └── assistance.py     # NEW: fixture-backed proposal seam + deterministic fallback (US6)
├── domain/
│   ├── components.py      # CHANGED: money/date compatibility (US1)
│   ├── projection.py      # CHANGED: per-item collection compose (US1)
│   └── health.py          # CHANGED: rule-based confidence/consistency/specificity (US3)
├── ports/
│   ├── option_provider.py # NEW: named option provider protocol (US1)
│   ├── output_adapter.py  # NEW: validate/preview/publish protocol (US2)
│   └── assistance.py      # NEW: narrow assistance protocol (US6)
├── infrastructure/
│   ├── adapters/          # NEW: json_document.py, registry.py (US2, US5)
│   ├── options/           # NEW: component_catalog provider + registry (US1)
│   └── assistance/        # NEW: fixture provider (US6)
├── api/routers/
│   ├── sessions.py        # CHANGED: add preview + publications endpoints (US2)
│   └── questionnaires.py  # CHANGED: expose decision resolution + raw JSON path (US4)
└── migrations/versions/   # NEW: published-artifact store migration (US2)

frontend/src/
├── components/renderers/
│   ├── registry.ts        # CHANGED: map MoneyField + DateTimeField (US1)
│   └── RepeatableGroup.vue # CHANGED: recursive nested-collection rendering (US1)
├── components/publication/PublicationReview.vue  # NEW: preview + publish exact revision (US2)
├── composables/usePublication.ts                 # NEW (US2)
└── router/index.ts        # CHANGED: publication route; meta-questionnaire session route (US5)

data/
├── contracts/v1/          # CHANGED: dynamic option source + meta output contract schema (US1, US5)
└── definitions/meta/      # NEW: bootstrapped meta-questionnaire (US5)
```

**Structure Decision**: Keep the one-backend/one-frontend layout. The self-hosted builder (US5) is a Qava questionnaire rendered by the existing runtime client — no new authoring app, no bespoke builder UI. New work lands as small ports + infrastructure implementations plus focused domain edits.

## Ownership Rules (unchanged from `001`, restated briefly)

1. Routers parse, authorize, invoke one application use case, and map errors; no domain logic.
2. Application services own transactions and return one complete session view.
3. Domain services are pure functions; new option/adapter/assistance behavior lives behind ports.
4. The client never derives mappings, health, readiness, or next interaction; it replaces state from each server response.
5. OpenAPI stays the client transport source; generated files are not hand-edited.

## Delivery Slices

Slices follow spec priority; each keeps the deterministic loop runnable and is independently testable.

| Slice | Story | Adds | Gate |
|---|---|---|---|
| 1 | US1 (P1) | Named option provider + registry; per-item collection compose; money/date compatibility and renderer mapping | A contract using runtime options, a nested collection, and money/date publishes and completes with every stored value typed and stable |
| 2 | US2 (P2) | `output_adapter` port; JSON document adapter + published-artifact store; preview + `POST /publications`; idempotency + receipts; resolvable `outcome_unknown` reconciliation | Ready revision previews side-effect-free, publishes once, returns a receipt; repeated key and stale revision are rejected with no duplicate artifact; an indeterminate outcome reconciles to a terminal status without a duplicate |
| 3 | US3 (P3) | Fixed rule-based confidence/consistency/specificity (author weights/gates unchanged); attention items; optional adapter dry-run in validity | Targeted weak-evidence, contradiction, and imprecision cases move the right dimension with concrete attention |
| 4 | US4 (P4) | Explicit confirm/override/reject decision workflow; raw JSON authoring path through the same gate | An ambiguous decision resolves both ways and both routes converge on identical publication validation |
| 5 | US5 (P5) | Meta output contract (published-questionnaire schema); bootstrapped meta-questionnaire; registry adapter | A five-question questionnaire is authored, published, and run through Qava itself and registers a new version |
| 6 | US6 (P6) | `assistance` port + fixture provider + audit metadata; deterministic fallback wiring | Fixtures return validated proposals; disabling them leaves every path deterministic and correct; a real provider could drop in behind the port |

## Task Generation Guardrails

- Generate tasks in slice order; complete and keep each slice runnable before the next.
- Every implementation task names an exact file path and one observable outcome, with a paired test task at any contract/mapping/projection/health/publication/immutable-version boundary.
- Reuse the existing custom-home fixture; add a fixture only for a genuinely new answer shape.
- Create no adapter beyond JSON document and registry; no provider framework beyond one protocol + one fixture; no bespoke authoring builder UI.
- Python tasks load `fastapi-python` + `python-best-practices`; Vue tasks load `vue-best-practices` (and `vue-router-best-practices` when routing changes) + `qava-cirrus-design`.

## Complexity Tracking

No violations. The feature adds three narrow port families, two required adapters, and focused domain edits, reusing existing storage scaffolding and the runtime client for self-hosted authoring.
