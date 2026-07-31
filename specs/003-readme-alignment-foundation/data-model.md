# Data Model: README Alignment Foundation

## Overview

This feature defines planning and traceability entities, not runtime domain entities. These
entities describe alignment status, reusable foundations, coupling rules, and delivery sequencing.

## Entities

### 1. AlignmentCapabilityRecord

Tracks one README aspiration area against current implementation.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable unique identifier per aspiration area |
| `aspiration_area` | string | Human-readable README capability area |
| `status` | enum | One of `implemented`, `partial`, `missing` |
| `evidence_refs` | string array | At least one reference to supporting artifacts |
| `scope_note` | string | Clarifies current boundary and interpretation |
| `next_action` | string | Required when status is `partial` or `missing` |
| `owner` | string | Responsible role or team |
| `last_reviewed_at` | datetime string | Updated whenever status is re-evaluated |

Validation rules:
- `status` must be explicit and never inferred implicitly.
- `evidence_refs` cannot be empty.
- `next_action` is mandatory unless `status` is `implemented` with no pending follow-up.

### 2. FoundationElementDefinition

Defines one reusable building block and how future work composes with it.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable unique foundation key |
| `name` | string | Clear reusable element name |
| `layer` | enum | `api`, `application`, `domain`, `infrastructure`, `transport`, `frontend` |
| `responsibility` | string | Single primary purpose statement |
| `contract_boundary` | string | Declares what is guaranteed to consumers |
| `owned_by` | string | Steward role/team |
| `extension_seams` | string array | Enumerates approved extension points |
| `reuse_examples` | string array | Existing capability examples using this element |

Validation rules:
- Responsibility must be singular and non-overlapping with peer foundations.
- At least one extension seam must be declared.
- Contract boundary must be specific enough for review decisions.

### 3. CouplingRule

Defines allowed and disallowed dependency interactions.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable rule identifier |
| `from_layer` | enum | Source layer |
| `to_layer` | enum | Target layer |
| `mode` | enum | `allowed`, `restricted`, `prohibited` |
| `rule_text` | string | Clear policy statement |
| `review_check` | string | How compliance is verified |

Validation rules:
- `prohibited` rules require explicit review checks.
- `restricted` rules must include accepted exception criteria.

### 4. RoadmapSlice

Represents one implementation increment linked to alignment gaps.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable slice identifier |
| `title` | string | Outcome-focused name |
| `target_gaps` | string array | One or more `AlignmentCapabilityRecord.id` values |
| `reused_foundations` | string array | One or more `FoundationElementDefinition.id` values |
| `extended_seam` | string | Single declared extension seam |
| `preserved_behaviors` | string array | Existing behaviors that must not regress |
| `contract_checks` | string array | Required checks before and after completion |
| `risk_flags` | string array | Known dependency/coupling risks |
| `status` | enum | `planned`, `in-progress`, `done` |

Validation rules:
- Every slice must name reused foundations and one seam.
- Every slice must include preserved behavior checks before approval.
- `done` slices require alignment status review update.

## Relationships

- `RoadmapSlice.target_gaps` -> `AlignmentCapabilityRecord.id` (many-to-many)
- `RoadmapSlice.reused_foundations` -> `FoundationElementDefinition.id` (many-to-many)
- `CouplingRule` governs validity of `RoadmapSlice` dependency behavior

## State Transitions

### AlignmentCapabilityRecord.status

`missing` -> `partial` -> `implemented`

Rules:
- Transition requires updated evidence references.
- Transition to `implemented` requires no unresolved blocking next action.

### RoadmapSlice.status

`planned` -> `in-progress` -> `done`

Rules:
- `planned` -> `in-progress` requires coupling risk check complete.
- `in-progress` -> `done` requires contract checks pass and alignment review recorded.
