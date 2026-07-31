# Phase 1 Data Model: README Gap Closure

Only new or changed entities are listed. Existing entities (`OutputNeed`, `Question`, `Mapping`, `SessionRecord`, `ResultProjection`, `HealthAssessmentRecord`, `PublishedQuestionnaireRecord`) are reused unchanged except where noted.

## New

### DynamicOptionSource (US1)

Runtime source for a question's choices, resolved through the provider registry.

- `provider` — name of a registered provider (initial: `component_catalog`).
- `params` — optional provider-scoped lookup parameters.
- Yields `choices: [{ id, label }]` where `id` is the stable stored value.
- Validation: provider must be registered; yielded `id`s must satisfy the question's answer schema.

### PublishedArtifact (US2)

Immutable output of the JSON document adapter.

- `artifact_id`, `session_id`, `questionnaire_id`, `revision`.
- `data` — the canonical result JSON at the published revision.
- `created_at`.
- Immutable once written; referenced by a publication receipt's internal reference.

### OutputAdapter contract (US2, US5) — port, not stored

- `validate(result, destination_config) -> issues[]`
- `preview(result) -> result` (side-effect free)
- `publish(result, idempotency_key) -> receipt`
- Implementations: `json_document` (writes a `PublishedArtifact`), `registry` (writes a new `PublishedQuestionnaireRecord` version).

### AuthoringDecision (US4)

An ambiguous or low-confidence draft decision requiring explicit resolution.

- `decision_id`, `draft_id`, `kind` (e.g., component choice, mapping).
- `candidates` — allowed options with confidence/reasons.
- `status` — `pending` | `confirmed` | `overridden` | `rejected`.
- `resolution` — chosen value when confirmed/overridden.
- Rule: a draft with any `pending` blocking decision cannot publish.

### MetaQuestionnaire (US5) — data, not a new type

- The published-questionnaire JSON Schema used as an output contract.
- Its result projection is a valid questionnaire document published via the registry adapter, returning `{ id, version }`.

### AssistanceProposal (US6) — reuses existing `assistance_proposals` table

- `proposal_id`, `session_id` (or draft), `operation` (`component` | `ranking` | `question` | `clarification` | `extraction`).
- `payload` — the proposed value with `confidence` and `reasons`.
- `status` — validated / rejected / applied.
- `audit` — placeholder `model_identity`, `policy_version`, `evidence` (fixture values in this feature).

## Changed

### PublicationRecord / receipt (US2)

- Existing model reused. Populated fields on success: `adapter`, `destination`, `revision`, `status`, `idempotency_key`, `external_reference` (internal artifact reference), `created_at`, `completed_at`.
- Idempotency: a repeated `idempotency_key` returns the prior receipt with no new artifact.
- Indeterminate outcome: an attempt whose adapter result is unknown is recorded with `status = outcome_unknown` and is resolvable via an explicit reconciliation that transitions it to a terminal status (`succeeded`/`failed`) without creating a duplicate artifact.

### HealthAssessmentRecord dimensions (US3)

- `confidence`, `consistency`, `specificity` change from placeholder heuristics to fixed, built-in, inspectable rule outputs.
- Each non-perfect dimension emits an attention item with `code`, `severity`, `message`, `recommended_action`, and supporting evidence.
- `validity` may include an optional adapter dry run so blocking structural errors surface pre-publish.

### Question presentation (US1)

- Adds recognition of money and date/time components in `domain/components.py` compatibility, and per-item compose mapping in `domain/projection.py` for nested collections within existing depth/item limits.
