# Phase 0 Research: README Gap Closure

Decisions are intentionally small — most were fixed during `/speckit.clarify`. Each records what was chosen, why, and the alternative rejected.

## D1. Feature scope and the agent layer

- **Decision**: Deliver US1–US5 as real behavior; include US6 as an interface plus hardcoded fixture responses with deterministic fallback — no real AI provider.
- **Rationale**: The agent layer is the largest but least urgent gap and depends on earlier slices only through seams. Reserving the seam now proves the policy/fallback contract cheaply and lets a real provider drop in later.
- **Alternatives rejected**: Building a real LLM integration now (large, premature, and unnecessary for MVP correctness); omitting the seam entirely (would force a contract change later).

## D2. JSON document adapter side effect

- **Decision**: `publish` persists the canonical result as an immutable published-artifact record in Qava's own store; the receipt carries an internal reference.
- **Rationale**: Smallest change that proves the explicit-side-effect + durable-receipt model, mirrors how the registry adapter writes versions, and needs no external infrastructure.
- **Alternatives rejected**: Filesystem file, external HTTP POST (add environment coupling before the JSON path is proven); inline-only receipt (no durable artifact, fails the "delivered artifact" intent).

## D3. Dynamic option source providers

- **Decision**: A loosely coupled provider-registry seam with one initial provider — the component catalog. More providers register later without changing consumers.
- **Rationale**: Exactly satisfies self-hosting (US5, "which component?" options) with minimal surface and low coupling.
- **Alternatives rejected**: Hardcoded catalog lookup (no seam for growth); a general external/HTTP source registry now (over-built before need).

## D4. Authoring UI extent

- **Decision**: No bespoke authoring builder. US4 delivers the backend confirm/override/reject workflow plus a raw JSON path; the guided experience is US5's meta-questionnaire rendered by the existing runtime client.
- **Rationale**: Matches the README self-hosting thesis (a questionnaire that builds a questionnaire), reuses the renderer, and avoids throwaway UI.
- **Alternatives rejected**: A dedicated visual builder (redundant with self-hosting, high cost); a minimal draft-management UI (still throwaway once US5 lands).

## D5. Health dimension rule source

- **Decision**: A fixed, built-in, published, inspectable rule set for confidence, consistency, and specificity — no author configuration, no per-questionnaire defaults.
- **Rationale**: Makes scores deterministic and testable without expanding the health-policy schema; keeps the change contained to `domain/health.py`.
- **Alternatives rejected**: Author-declared rules (larger data-model surface); global heuristics that stay non-inspectable (fails the explainable-health gate).

## D6. Reuse of existing storage scaffolding

- **Decision**: Reuse the existing `publication_attempts` and `assistance_proposals` tables and repository protocols rather than redesigning them; add only a published-artifact store table.
- **Rationale**: The scaffolding already matches the required receipt/idempotency and proposal shapes; wiring services to it is the missing piece.
- **Alternatives rejected**: New schema design (unnecessary churn and migration risk).

## Open items

None. All spec `[NEEDS CLARIFICATION]` were resolved in the clarify session; health-dimension exact thresholds are an implementation detail captured as tasks, not open questions.
