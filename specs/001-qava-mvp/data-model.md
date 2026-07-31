# Data Model: Qava MVP

**Feature**: `001-qava-mvp`
**Date**: 2026-07-25

## Modeling Rules

- JSON Schema Draft 2020-12 is authoritative for output contracts and answer values.
- Published questionnaire content, accepted answers, interactions, and publication receipts are immutable records.
- The session row is the authoritative current snapshot; projections, applicability, health, and next candidates are derived during a mutation transaction.
- Stable IDs are opaque strings. Questionnaire versions and session revisions are positive integers.
- Times are UTC ISO 8601 values.
- Runtime records remain until authorized session deletion. External artifacts are never retracted by session deletion.
- Keep the relational model small. Store immutable structured documents as JSON text and index only fields needed for identity, lifecycle, concurrency, authorization, and idempotency.

## Authoring Models

### OutputContract

The desired canonical result shape.

| Field | Type | Rules |
|---|---|---|
| `schema` | JSON object | Valid Draft 2020-12 schema; local/approved references only |
| `schema_hash` | string | SHA-256 of canonicalized schema |

Validation:

- Root MUST describe a JSON object for the MVP.
- Required fields and accepted values come only from the schema.
- Unsupported or unsafe references block publication.

### OutputNeed

An addressable value requirement derived during compilation. It is embedded in a questionnaire document, not stored as a separate table.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable and unique within questionnaire version |
| `target` | JSON Pointer | Must resolve to an addressable output location |
| `value_schema` | JSON object | Schema accepted at target |
| `required` | boolean | Derived from output contract |
| `criticality` | enum | `normal`, `blocking` |
| `weight` | number | Positive health weight |

### Question

A typed request for evidence embedded in a draft or published questionnaire.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique within questionnaire version |
| `output_need_ids` | string array | At least one existing output need |
| `prompt` | string | Non-empty |
| `help_text` | string or null | Optional |
| `answer_schema` | JSON object | Valid Draft 2020-12 schema |
| `choices` | choice array or null | Unique stable IDs; labels are display-only |
| `mapping` | Mapping | Direct or compose only |
| `applicability` | Condition or null | Small declared vocabulary only |
| `presentation` | ComponentSpec | Must resolve against catalog |
| `required` | boolean | Cannot contradict served blocking need |
| `order` | integer | Deterministic fallback order |
| `clarification_policy` | object | Maximum follow-ups 0-2 |

### Mapping

| Variant | Fields | Rules |
|---|---|---|
| Direct | `mode`, `target` | One accepted answer writes one declared target |
| Compose | `mode`, `target`, `sources`, `shape` | Declared answers compose one object or array; no arbitrary code |

Mapping targets MUST exist in the output contract. Conflicts block publication.

### Condition

| Field | Type | Rules |
|---|---|---|
| `source_question_id` | string | Existing earlier or independent question |
| `operator` | enum | `equals`, `contains`, `exists` |
| `value` | JSON value or omitted | Required only where operator needs it |

Conditions are deterministic. General expressions and scripts are excluded.

Evaluation rules:

- `equals`: JSON values are equal without type coercion. The string `"1"` does not equal number `1`.
- `contains`: for an array, the condition value is an equal member; for a string, the condition
  value is a substring. Other source types evaluate false.
- `exists`: the source answer exists and is not JSON `null`. Empty string, `false`, `0`, and empty
  collections still exist.
- An inactive answer is retained audit evidence whose question is currently inapplicable; it is
  excluded from projection and condition inputs. A missing, invalid, or inactive source answer
  makes the condition false.

### ComponentSpec

| Field | Type | Rules |
|---|---|---|
| `name` | string | Existing component catalog ID |
| `version` | integer | Supported catalog component version |
| `props` | JSON object | Valid against catalog props schema |
| `fallback` | string or null | Declared schema-compatible component only |

The component catalog is an engine build-time/runtime resource, not a separate public API resource.
The server validates and resolves a complete component specification into each session view. The
Vue registry implements the same checked-in catalog version. Self-hosted authoring receives live
catalog choices through the normal named dynamic-option provider contract.

### HealthPolicy

Published, inspectable health and readiness rules.

| Field | Type | Rules |
|---|---|---|
| `calculation_version` | integer | Positive algorithm version |
| `weights` | five positive numbers | completeness, validity, confidence, consistency, specificity |
| `publication_gate.require_all_required` | boolean | MUST be true in MVP |
| `publication_gate.minimum_validity` | integer | 0-100 |
| `publication_gate.block_on` | enum | `blocking` or `warning` |

Readiness requires all required output needs, validity at or above the configured minimum, and no
attention item at or above `block_on`. The headline score never overrides these checks.
The headline score is the weighted sum of dimension scores divided by the sum of configured
weights; weights need not sum to 100.

### AssistancePolicy

| Field | Type | Rules |
|---|---|---|
| `enabled_operations` | enum array | authoring, ranking, clarification, extraction |
| `maximum_clarifications_per_interaction` | integer | 0-2 |
| `maximum_generated_interactions_per_session` | integer | 0-1,000 |
| `timeout_ms` | integer | Positive; timeout triggers deterministic fallback |
| `require_extraction_confirmation` | boolean | MUST be true in MVP |

An operation not listed is prohibited. Policy limits are copied into generated interactions for
audit and reproducibility.

### QuestionnaireDraft

Mutable authoring state.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Kebab-case stable identity |
| `base_version` | integer or null | Version copied for editing, if any |
| `title` | string | Non-empty |
| `description` | string | Optional |
| `output_contract` | OutputContract | Required |
| `output_needs` | array | Derived/rebuilt during compilation |
| `questions` | array | Authored and proposed questions |
| `health_policy` | HealthPolicy | Required before publication |
| `assistance_policy` | AssistancePolicy | Explicit enabled operations and limits |
| `decisions` | AuthoringDecision array | Pending/accepted/rejected proposals |
| `validation_issues` | Issue array | Derived on validation |
| `updated_at` | datetime | UTC |

State transitions:

```text
draft -> validated -> published
  ^         |
  └-- edit -┘
```

Any edit returns the draft to `draft`. Only an explicit publish action can create a published version.

### AuthoringDecision

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable draft-local ID |
| `kind` | enum | question, mapping, component, policy |
| `proposal` | JSON object | Typed by kind |
| `confidence` | number | 0-1 for assisted proposals |
| `reasons` | string array | At least one for assisted proposals |
| `status` | enum | pending, accepted, overridden, rejected |
| `resolved_by` | identity ID or null | Required when resolved |

### PublishedQuestionnaire

Immutable runtime package.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable identity |
| `version` | integer | Monotonically increasing per ID |
| `schema_version` | integer | Engine contract version |
| `title` | string | Non-empty |
| `output_contract` | OutputContract | Embedded |
| `output_needs` | array | Embedded |
| `questions` | array | Embedded |
| `component_catalog_version` | integer | Exact catalog version |
| `health_policy` | HealthPolicy | Embedded |
| `assistance_policy` | AssistancePolicy | Embedded |
| `allowed_result_adapters` | string array | `json-document` only in MVP |
| `content_hash` | string | Unique immutable content hash |
| `published_by` | identity ID | Author role required |
| `published_at` | datetime | UTC |

Publication validation MUST cover all links, mappings, choices, components, conditions, limits, policies, and required output satisfiability.

## Runtime Models

### Session

Authoritative mutable snapshot.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Opaque unique ID |
| `questionnaire_id` | string | Existing published identity |
| `questionnaire_version` | integer | Exact immutable version |
| `revision` | integer | Starts at 1; increments once per accepted mutation |
| `status` | enum | active, completed; deletion hard-removes the session row |
| `active_topic_id` | string or null | Declared questionnaire topic; "section" in the spec means topic |
| `answers` | object keyed by question ID | Latest accepted answer records |
| `generated_interactions` | array or references | Session-scoped, policy-bound interactions |
| `created_by` | identity ID | Respondent permission required |
| `created_at` | datetime | UTC |
| `updated_at` | datetime | UTC |

Invariant: updates use `WHERE id = ? AND revision = expected_revision`; exactly one updated row means success.

Topics provide grouping and navigation only in the MVP. The complete session view exposes global
requirement progress plus the active topic and topic IDs on unresolved needs; it does not calculate
or persist separate per-topic progress or health.

Generated interaction lifecycle:

- A normal `question` is selected from the immutable published questionnaire; showing it creates
  only an interaction record.
- A `clarification` is a persisted session-scoped interaction created when published policy permits
  more evidence for an existing answer. It cannot create an output need or change accepted shape.
- A `review` is a persisted session-scoped interaction created when an edit makes accepted evidence
  inapplicable or conflicting. It asks the respondent to confirm or replace existing evidence.
- A `confirmation` is a persisted session-scoped interaction that asks the respondent to accept or
  reject a schema-valid extraction proposal before it may become an accepted answer.
- Every generated interaction stores its reason, served output needs, schema-compatible component,
  originating interaction, generation count, and applicable policy limits before it is shown.

### AcceptedAnswer

Stored inside the session snapshot and copied into append-only interaction evidence.

| Field | Type | Rules |
|---|---|---|
| `question_id` | string | Existing or persisted generated interaction |
| `output_need_ids` | string array | Declared bindings |
| `value` | JSON value | Valid against answer schema |
| `display_value` | JSON value or null | Convenience only |
| `source` | enum | user, confirmed_extraction |
| `accepted_by` | identity ID | Host identity |
| `accepted_at_revision` | integer | New session revision |
| `accepted_at` | datetime | UTC |

Answer validation is strict Draft 2020-12 validation with no type coercion. All schema keywords are
enforced. For declared choices, the machine value MUST equal a choice ID; display labels are never
accepted as substitutes. Collection schemas MUST declare `maxItems` no greater than 100, and
publication validation rejects collection nesting deeper than 3.

### InteractionRecord

Append-only explanation of what happened.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique |
| `session_id` | string | Existing session |
| `session_revision` | integer | Revision produced or observed |
| `kind` | enum | question_shown, answer_accepted, answer_rejected, skip, clarification, confirmation, review, navigation, assistance_fallback |
| `interaction_snapshot` | JSON object | Persisted prompt/schema/component where relevant |
| `submitted_value` | JSON value or null | Retained for accepted/rejected audit according to policy |
| `actor_id` | identity ID or system | Required |
| `metadata` | JSON object | Typed by kind: reason/policy for generated interactions; validation codes for rejection; target for navigation; provider/model/policy for fallback |
| `created_at` | datetime | UTC |

### ResultProjection

Derived for every session revision and returned in the session view.

| Field | Type | Rules |
|---|---|---|
| `session_id` | string | Existing session |
| `revision` | integer | Exact session revision |
| `status` | enum | in_progress, ready, published |
| `data` | JSON object | Canonical output draft |
| `provenance` | object keyed by JSON Pointer | Supporting answer IDs and interaction IDs |
| `unresolved_output_needs` | OutputNeedSummary array | ID, label/target, required, criticality, and navigable question/topic |
| `issues` | Issue array | Mapping and contract validation issues |

The projection is not stored as an independent mutable aggregate. It may be cached in the session snapshot only as a revision-keyed optimization.

### HealthAssessment

Derived using the questionnaire's published policy.

| Field | Type | Rules |
|---|---|---|
| `revision` | integer | Exact session revision |
| `score` | integer | 0-100 weighted headline |
| `readiness` | enum | not_ready, needs_attention, ready |
| `dimensions.completeness` | integer | 0-100 |
| `dimensions.validity` | integer | 0-100 |
| `dimensions.confidence` | integer | 0-100 |
| `dimensions.consistency` | integer | 0-100 |
| `dimensions.specificity` | integer | 0-100 |
| `attention` | AttentionItem array | Evidence-linked and actionable |
| `calculation_version` | integer | Published algorithm version |

`validity` replaces the seed fixture's `clarity` dimension to align with the ratified specification.

### AttentionItem

| Field | Type | Rules |
|---|---|---|
| `code` | string | Stable machine code |
| `severity` | enum | info, warning, blocking |
| `output_need_id` | string or null | Required where attributable |
| `message` | string | Human-readable |
| `recommended_action` | string | Concrete remediation |
| `evidence` | EvidenceRef array | Required for assisted observations |

### SessionView

Complete client contract returned after session reads and accepted mutations.

| Field | Type | Rules |
|---|---|---|
| `session` | SessionSummary | ID, version, revision, lifecycle |
| `progress` | Progress | Requirement-based counts |
| `current_interaction` | RuntimeInteraction or null | Exactly one active interaction |
| `result` | ResultProjection | Full canonical data and provenance |
| `health` | HealthAssessment | Same revision |
| `actions` | action enum array | Authorized and state-valid actions |
| `changed_paths` | JSON Pointer array | Paths changed by latest mutation |

All revision-bearing children MUST match `session.revision`.

### RuntimeInteraction

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable defined ID or persisted generated ID |
| `kind` | enum | question, clarification, confirmation, review |
| `output_need_ids` | string array | Existing IDs |
| `prompt` | string | Non-empty |
| `reason` | string | Why it matters to output |
| `required` | boolean | Explicit |
| `answer_schema` | JSON object | Authoritative accepted shape |
| `component` | ComponentSpec | Valid and renderable |
| `policy_limit` | RuntimePolicyLimit or null | Origin ID, generation index, maximum follow-ups, and session interaction cap; required for generated interaction |

Deterministic selection sorts eligible interactions by:

1. category: invalid/conflicting accepted evidence, required confirmation/review, unresolved
  required need, permitted clarification, useful optional need;
2. criticality: blocking before normal;
3. published question `order`;
4. stable interaction ID as the final tie-breaker.

Assistance may reorder only the resulting eligible set.

### AssistanceProposal

Untrusted structured input; never an accepted answer.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique |
| `operation` | enum | authoring, ranking, clarification, extraction |
| `payload` | typed union | Authoring question/component proposal; ordered eligible IDs; clarification interaction; or extracted value plus source evidence |
| `served_output_need_ids` | string array | Existing IDs only |
| `confidence` | number | 0-1 |
| `reasons` | string array | Required |
| `provider` | string | Provider identity |
| `model` | string or null | Model identity when applicable |
| `policy_version` | integer | Published policy |
| `status` | enum | proposed, accepted, rejected, invalid, fallback |
| `created_at` | datetime | UTC |

Every payload is a discriminated union by `operation`. Ranking payloads may contain only IDs from
the supplied eligible set. Clarification/extraction payloads must include originating interaction,
served output needs, evidence references, and policy limit. Invalid payloads are stored with status
`invalid` and trigger fallback.

### PublicationAttempt

Immutable attempt and idempotency record.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique |
| `session_id` | string | Existing session at attempt time |
| `session_revision` | integer | Exact requested revision |
| `adapter` | string | Allowed configured adapter |
| `idempotency_key` | string | Unique within adapter/destination scope |
| `status` | enum | validating, succeeded, failed, outcome_unknown, denied |
| `requested_by` | identity ID | Publisher role required |
| `destination` | string | Non-secret configured destination identity |
| `external_reference` | string or null | Adapter result |
| `error` | ProblemDetail or null | Sanitized failure |
| `created_at` | datetime | UTC |
| `completed_at` | datetime or null | UTC |

A successful attempt is the publication receipt. Repeating the same key returns the stored attempt without invoking the adapter.

Publication state transitions:

```text
request -> validating -> succeeded
                      -> failed          (adapter confirms no delivery)
                      -> outcome_unknown (timeout/connection loss after delivery may have occurred)
request -> denied                         (authorization fails before adapter invocation)
```

Only `succeeded` makes the exact result revision published. `outcome_unknown` blocks a new
idempotency key until an operator resolves the existing attempt; repeating the same key returns it.

MVP destination rules are fixed, not user-customizable: result publication uses `json-document`
to the server-configured artifact root, and questionnaire publication uses the internal
`questionnaire-registry`. Destination secrets and arbitrary paths never appear in questionnaires.

### JSONDocumentArtifact

MVP destination output.

| Field | Type | Rules |
|---|---|---|
| `artifact_id` | string | Stable generated ID |
| `session_id` | string | Source session |
| `session_revision` | integer | Exact source revision |
| `content_hash` | string | SHA-256 |
| `relative_path` | string | Under approved artifact root only |
| `created_at` | datetime | UTC |

Session deletion does not delete this artifact.

## Persistence Tables

Keep six tables for the MVP:

| Table | Purpose | Important constraints/indexes |
|---|---|---|
| `questionnaire_drafts` | Current mutable authoring documents | primary `id`; JSON document; updated time |
| `published_questionnaires` | Immutable runtime packages | primary `(id, version)`; unique content hash |
| `sessions` | Authoritative current snapshots | primary `id`; indexed status; revision compare-and-swap |
| `interactions` | Append-only session evidence | primary `id`; index `(session_id, created_at)` |
| `assistance_proposals` | Auditable untrusted proposals | primary `id`; index `(session_id, status)` |
| `publication_attempts` | Idempotency and immutable outcomes | primary `id`; unique `(adapter, destination, idempotency_key)`; index session/revision |

JSON document artifacts live under an approved artifact directory. No generic asset-upload store is added until file-upload behavior is implemented by an explicit task.

## Deletion Transaction

Authorized session deletion performs one database transaction:

1. Read successful publication count and return a warning/confirmation requirement if not already confirmed.
2. Compare and increment the expected session revision.
3. Delete assistance proposals, interactions, publication attempts, and the session snapshot.
4. Commit.
5. Leave all JSON document artifacts untouched.

Deletion is not an `InteractionRecord`, because all session interactions are removed. Qava emits a
structured security log containing only session ID, actor ID, and deletion time to the host logging
sink; it does not add another persistent audit store.

## Cross-Entity Invariants

1. Every session pins one immutable published questionnaire version.
2. Every accepted value validates against its persisted interaction answer schema.
3. Every projected path points to declared output contract data and supporting accepted answers.
4. Every health assessment and result projection uses the same session revision.
5. Assistance can reorder only an already deterministic eligible set.
6. Publication validates and delivers one exact revision and never follows later session changes.
7. Published questionnaire and successful publication records are never updated in place.
8. Client display labels never replace stable machine values.
