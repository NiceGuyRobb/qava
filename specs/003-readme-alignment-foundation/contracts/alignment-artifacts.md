# Contract: Alignment Artifacts

This contract defines required structure for README-alignment planning artifacts so they are
consistent, reviewable, and reusable.

## 1) Alignment Capability Record Contract

Required fields:
- `id`
- `aspiration_area`
- `status`
- `evidence_refs`
- `scope_note`
- `owner`
- `last_reviewed_at`

Conditional fields:
- `next_action` required when `status` is `partial` or `missing`

Allowed status values:
- `implemented`
- `partial`
- `missing`

## 2) Foundation Element Definition Contract

Required fields:
- `id`
- `name`
- `layer`
- `responsibility`
- `contract_boundary`
- `owned_by`
- `extension_seams`

Allowed layer values:
- `api`
- `application`
- `domain`
- `infrastructure`
- `transport`
- `frontend`

## 3) Coupling Rule Contract

Required fields:
- `id`
- `from_layer`
- `to_layer`
- `mode`
- `rule_text`
- `review_check`

Allowed mode values:
- `allowed`
- `restricted`
- `prohibited`

## 4) Roadmap Slice Contract

Required fields:
- `id`
- `title`
- `target_gaps`
- `reused_foundations`
- `extended_seam`
- `preserved_behaviors`
- `contract_checks`
- `risk_flags`
- `status`

Allowed status values:
- `planned`
- `in-progress`
- `done`

## 5) Review Rules

- Every roadmap slice must reference at least one target gap and one reused foundation.
- Every status update to `done` must trigger an alignment capability review update.
- Any prohibited coupling in a slice is a blocking review failure unless the governing rule is amended.
