# Quickstart: README Alignment Foundation

This quickstart validates the planning feature artifacts end to end.

## Prerequisites

- Repository checked out with current feature branch
- Access to:
  - `README.md`
  - `specs/001-qava-mvp/*`
  - `specs/002-deterministic-runtime-hardening/*`
  - `openapi/qava.openapi.json`

## Validation Scenario A: Build an Alignment Baseline

1. Enumerate major README aspiration areas.
2. Create one `AlignmentCapabilityRecord` per area using the contract in:
   - `contracts/alignment-artifacts.md`
3. For each record, assign `implemented`, `partial`, or `missing` and attach evidence references.
4. Confirm every `partial`/`missing` record has a `next_action`.

Expected outcome:
- 100% aspiration coverage with evidence-backed status (SC-001, SC-002).

## Validation Scenario B: Define Minimal Foundations and Coupling Rules

1. Create a `FoundationElementDefinition` list using current architecture seams.
2. Create `CouplingRule` entries for allowed/restricted/prohibited directions.
3. Verify each foundation has a single responsibility and at least one extension seam.

Expected outcome:
- Reusable foundation catalog that can be applied to future slices without adding architecture layers.

## Validation Scenario C: Produce First Executable Roadmap Slice

1. Create one `RoadmapSlice` targeting at least one `partial` or `missing` gap.
2. Reference reused foundations and one extended seam.
3. List preserved behaviors and contract checks.
4. Mark unresolved dependency/coupling risks.

Expected outcome:
- Slice is implementation-ready without extra clarification (SC-004).

## Exit Criteria

- Alignment baseline exists and is reviewable by technical and non-technical stakeholders.
- Foundation and coupling contracts are applied consistently.
- First roadmap slice is ready for `/speckit.tasks` generation.
