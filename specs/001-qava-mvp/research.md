# Phase 0 Research: Qava MVP

**Feature**: `001-qava-mvp`
**Date**: 2026-07-25

## Backend Runtime

**Decision**: Use Python 3.12 with FastAPI, Pydantic v2, and Uvicorn.

**Rationale**: FastAPI exposes typed asynchronous HTTP boundaries and OpenAPI 3.1 from the same Pydantic request and response models. Python 3.12 satisfies the workspace Python guidance, has mature library support, and keeps the engine, application services, and adapters in one language.

**Alternatives considered**:

- Django REST Framework: useful built-in administration, but adds an ORM and application model broader than this contract-first engine requires.
- Starlette directly: smaller runtime, but recreates validation, dependency injection, and OpenAPI integration already supplied by FastAPI.
- Node backend: duplicates the requested Python implementation and loses the installed FastAPI/Python practice guidance.

## Contract Validation

**Decision**: Keep JSON Schema Draft 2020-12 files authoritative; use `referencing` plus `jsonschema` for schema registry and validation, with Pydantic models at API and persistence boundaries.

**Rationale**: Output contracts and dynamic answer schemas cannot be reduced to static Python types. JSON Schema remains the source of truth, while Pydantic provides typed transport objects. Schema resources are loaded into an explicit registry so validation never performs unbounded network retrieval.

**Alternatives considered**:

- Pydantic-only validation: cannot faithfully validate arbitrary author-provided JSON Schema.
- Hand-written validators: duplicate a standard and increase correctness risk.
- Runtime remote `$ref` retrieval: creates availability and trust problems; approved local resources are safer and reproducible.

## Existing Contract Migration

**Decision**: Treat `data/contracts/v1` as seed contracts that require a deliberate compatibility update before implementation. Preserve stable concepts and fixture value, but align them with the ratified specification.

**Rationale**: Existing files already establish manifest, question, interaction, session, and evidence vocabulary. However, the session schema currently uses `clarity` where the ratified MVP requires `validity`, its statuses do not express readiness/publication, and its condition operators are broader than the current constitution/spec vocabulary. Contract changes must be explicit, validated, and reflected in examples rather than hidden in code.

**Alternatives considered**:

- Implement existing files unchanged: conflicts with the ratified specification.
- Delete and regenerate all data: discards useful fixtures and stable identifiers.
- Create contract v2 immediately: premature until the compatibility effect of the changes is assessed during implementation; v1 may still be amended because no runtime release exists.

## Persistence and Concurrency

**Decision**: Use SQLAlchemy 2 asynchronous repositories over SQLite in WAL mode for the single-tenant MVP, with Alembic migrations and one application worker. Store immutable structured snapshots as JSON text plus indexed relational identity, revision, status, and idempotency fields.

**Rationale**: One tenant, at most 100 active sessions, and short transactional mutations fit SQLite while avoiding a required database service. An atomic `UPDATE ... WHERE revision = expected_revision` enforces stale-write rejection. A unique idempotency key enforces publication deduplication. Repository protocols keep a later PostgreSQL adapter possible without changing engine services.

**Alternatives considered**:

- PostgreSQL from day one: stronger multi-writer scale, but adds operational infrastructure not required by the clarified MVP.
- Files as runtime storage: cannot safely enforce transactional revisions or idempotent publication.
- Full event sourcing: unnecessary; session snapshots are authoritative and interactions provide append-only explanation.

## Engine Boundaries

**Decision**: Build pure domain services for definition compilation, condition evaluation, answer validation, projection, health, eligibility, and component resolution. Application services coordinate repositories and adapters; FastAPI routes remain transport-only.

**Rationale**: Pure functions make deterministic behavior directly testable and keep infrastructure out of the core loop. The existing `docs/data-layout.md` already proposes these boundaries, and they match the constitution's simple runtime model.

**Alternatives considered**:

- Logic in route handlers: couples HTTP to engine correctness and makes deterministic fallback harder to test.
- Generic workflow/graph engine: explicitly outside scope.
- Domain-specific services for the home example: violates engine neutrality.

## Agent Assistance

**Decision**: Define a small typed `AssistanceProvider` protocol for authoring proposals, bounded interaction ranking, clarification, and extraction proposals. Ship deterministic disabled and fixture providers. Defer external model-provider integration until the fixture-assisted path and deterministic fallback pass acceptance.

**Rationale**: The protocol makes untrusted assistance replaceable and ensures the deterministic candidate set exists before ranking. Timeouts, malformed output, undeclared identifiers, and policy violations all fall back to deterministic ordering.

**Alternatives considered**:

- A general agent framework: introduces unrestricted tools and orchestration contrary to the constitution.
- Direct provider calls in services or routes: spreads policy enforcement and weakens testing.
- No provider boundary: cannot demonstrate the required assisted path even though runtime operation remains deterministic.

## API Contract

**Decision**: Expose REST JSON under `/api/v1` with OpenAPI 3.1. Mutation responses return a complete `SessionView`. Use HTTP 409 for stale revisions and idempotency conflicts, 422 for typed validation or readiness failures, 403 for Qava permission failures, and problem-detail response bodies.

**Rationale**: The six runtime operations in the README map directly to resource-oriented endpoints. Complete views prevent frontend/client derived-state drift.

**Alternatives considered**:

- GraphQL: adds query and cache complexity without a variable client data need.
- WebSockets: unnecessary for the clarified single-user-per-session workflow; normal HTTP handles 100 active sessions.
- Separate partial mutation responses: require the client to recompute server-owned state.

## Host Identity

**Decision**: Accept a normalized identity context from trusted reverse-proxy headers only when requests originate through a configured trusted host boundary. Map claims to Qava roles (`author`, `respondent`, `publisher`) in a FastAPI dependency. Local development uses an explicit development identity provider, never an implicit anonymous production fallback.

**Rationale**: This implements the clarification without storing credentials. Central dependency enforcement keeps authorization consistent, and deployment configuration owns header integrity.

**Alternatives considered**:

- Built-in accounts: explicitly out of scope.
- Unsigned client-supplied identity headers on an exposed API: permits impersonation.
- No authorization: conflicts with authoring and publication requirements.

The normalized `X-Qava-Identity` value is a base64url-encoded UTF-8 JSON object with required
`subject` and `roles` fields, for example `{"subject":"user-123","roles":["respondent"]}`.
The reverse proxy strips inbound copies and writes the trusted header. Qava rejects malformed,
missing, or unknown-role contexts.

## Frontend Runtime

**Decision**: Use Vue 3.5 Composition API with `<script setup lang="ts">`, Vite, Vue Router 4, and Pinia. Use the generated OpenAPI TypeScript client for transport contracts and keep renderer answer values typed as `unknown` until schema/component-specific narrowing.

**Rationale**: This follows the installed Vue skill, supports focused semantic renderers, and prevents handwritten API type drift. Vue Router owns authoring and session route lifecycle; Pinia holds cross-route authoritative session and identity state, while local answer drafts stay in focused components/composables.

**Alternatives considered**:

- Options API: weaker TypeScript composition and contrary to workspace guidance.
- A large client query framework: unnecessary because every mutation replaces one complete authoritative view.
- Global state for every input: makes drafts and validation harder to isolate.

## Semantic Component Renderer

**Decision**: Implement a typed registry from catalog names to focused Vue components. A renderer receives prompt metadata, answer schema, and validated props; it emits a typed answer action and never performs mappings, next-question selection, health calculation, or publication.

**Rationale**: This is the client half of the existing component-catalog handshake and directly satisfies the typed-UI constitution principle. Unknown components fail explicitly unless the server declares a schema-compatible fallback.

**Alternatives considered**:

- Questionnaire-specific Vue forms: duplicate business logic and prevent generic rendering.
- Generate Vue source per questionnaire: explicitly outside scope.
- Convert unsupported values to strings: corrupts typed semantics.

## UX and Motion

**Decision**: Apply `.github/skills/qava-cirrus-design/SKILL.md`. Use a light atmospheric shell, compact operational surfaces, a desktop interview/result split, mobile `Question | Result | Health` views, full tree/raw canonical output, and evidence-linked health. Swap questions with keyed Vue `<Transition mode="out-in">` using only transform and opacity; honor reduced motion.

**Rationale**: This turns the user's "futuristic functional" direction into testable behavior while staying consistent with the publicly visible Cirrus concept. The full output remains a first-class work surface, not a decorative snippet.

**Alternatives considered**:

- Dark neon/cyberpunk UI: visually loud and weaker for prolonged operational use.
- Card-heavy dashboard: obscures the active interview and nests work surfaces.
- No transitions: loses useful orientation between adaptive interactions.
- Animation library for question swaps: Vue's built-in transition is sufficient and smaller.

## Result Preview

**Decision**: Provide synchronized tree and raw JSON modes, full-document scrolling, copy/download, revision labeling, JSON Pointer selection, and transient highlighting of paths changed by the latest accepted answer.

**Rationale**: Users asked for full current output. Pointer-level highlighting ties the answer to the output and supports provenance without blocking on a full diff engine.

**Alternatives considered**:

- Truncated preview: fails the explicit full-preview requirement.
- Raw JSON only: poor scanning for non-technical respondents.
- Side-by-side historical diff in MVP: useful later but adds substantial state and layout complexity.

## Testing

**Decision**: Use pytest, pytest-asyncio, HTTPX, and Hypothesis for backend unit/contract/integration tests; Vitest, Vue Test Utils, and `vue-tsc` for frontend logic/components; Playwright for end-to-end, accessibility, motion, responsive layout, screenshots, and full-preview validation; use a lightweight concurrent HTTP load test for SC-003.

**Rationale**: Boundary tests are constitution-required. Property tests are valuable for conditions, projections, and schema-derived values. Playwright directly verifies question transitions and visual behavior across desktop/mobile/reduced-motion modes.

**Alternatives considered**:

- Unit tests only: cannot prove contracts, persistence, client rendering, or publication.
- Snapshot-only UI tests: weak behavioral and accessibility coverage.
- Manual load testing: not repeatable as an acceptance gate.

## Tooling and Quality Gates

**Decision**: Manage Python with `uv` and `pyproject.toml`; use Ruff for lint/format and Pyright for static checks. Manage frontend with npm, ESLint, Prettier, and `vue-tsc`. Generate the TypeScript API client from OpenAPI in CI and fail on an uncommitted generated diff.

**Rationale**: This is a compact, fast toolchain with deterministic lockfiles and independent type checks on both sides of the API.

**Alternatives considered**:

- Multiple Python lint/format tools: more configuration with no MVP benefit.
- Hand-maintained client types: creates contract drift.
- Monorepo orchestrator: unnecessary for two applications.

## Deployment

**Decision**: Package one backend container that serves the built Vue assets and API, with a persistent volume for SQLite and published JSON artifacts. Run one Uvicorn worker for SQLite write serialization. Keep Vite and FastAPI as separate processes in development.

**Rationale**: One deployable unit matches the single-tenant MVP and keeps identity/trust boundaries clear. Static frontend and API share an origin in production.

**Alternatives considered**:

- Separate frontend hosting and API service: useful at larger scale, but adds CORS and deployment coordination now.
- Multiple backend workers with SQLite: creates avoidable write contention.
- Kubernetes: far beyond the clarified scale.

## Resolved Limits

**Decision**: Use contract-declared limits with platform caps: maximum collection nesting depth 3, maximum 100 items per collection, maximum 2 clarification follow-ups per originating interaction, and maximum 1,000 interactions per session.

**Rationale**: These limits cover self-hosted questionnaire collections and existing schema behavior while preventing unbounded recursion or agent loops. They are visible in publication validation and can become configurable in a later feature.

**Alternatives considered**:

- No limits: unsafe and untestable.
- Depth 1: cannot represent questionnaire -> questions -> choices in self-hosted authoring.
- Arbitrary scripts for conditions or transforms: explicitly outside scope.
