# Conceptual Model: Architecture Usage Diagram

This feature introduces documentation concepts only. It does not create application data, API objects, or persistence changes.

## Diagram Stages

| Stage | Role | Receives | Produces | Boundary to show |
|---|---|---|---|---|
| Declared output contract | Authoritative definition of the required artifact | Author intent and schema | Compiler input | Questions and AI do not redefine it |
| Compile and review | Authoring workspace | Contract, catalog, policy, optional proposals | Reviewed draft | Author confirms decisions; agent cannot publish |
| Published questionnaire | Stable runtime package | Explicit author publication | Immutable, versioned questionnaire | Runtime cannot mutate it |
| Render and answer | Respondent interaction | Declared component specification | Typed submitted value | Client renders and submits; engine decides correctness |
| Deterministic runtime | Core Qava engine | Questionnaire and accepted answer | Validated mapping, next interaction, result state | Validation, mappings, readiness, and policy are enforceable here |
| Canonical result and health | Continuous inspectable output | Recalculated runtime state | Draft, health, attention items, readiness | Preview is not an external side effect |
| Explicit publication | Authorized delivery action | A specific ready revision | Gate decision, adapter call, receipt | User authorization and gate precede side effects |

## Supporting Architectural Records

| Record | Lifecycle | Relationship to diagram |
|---|---|---|
| Published questionnaires | Immutable and versioned | Records the authoring output used by a session |
| Session snapshot and revisions | Authoritative evolving state | Supports resume and connects an answer cycle to its selected questionnaire version |
| Interactions | Append-only history | Explains shown questions, submitted answers, clarifications, reviews, skips, and navigation |
| Publication attempts and receipts | Immutable audit evidence | Records the explicit delivery request and the adapter outcome |

## Relationship Rules

1. The contract compiles into a reviewed questionnaire; an author publishes the questionnaire before a respondent can start a session.
2. A session pins one published questionnaire version. The client renders its declared component and sends a typed value to the deterministic runtime.
3. The runtime validates and maps an accepted answer, then recalculates the result, provenance, health, attention items, readiness, and next eligible interaction.
4. The bounded agent can provide policy-constrained proposals or ranking and clarification assistance. Deterministic eligibility and ordering continue when the agent is unavailable or invalid.
5. The canonical draft can be inspected after every accepted answer. Only an explicitly authorized ready revision passes through a publication gate and adapter to create a destination artifact and receipt.