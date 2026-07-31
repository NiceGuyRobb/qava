# Implementation Plan: README Alignment Foundation

**Branch**: `003-readme-alignment-foundation` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-readme-alignment-foundation/spec.md`

## Summary

Create a lightweight, evidence-backed alignment baseline between README aspirations and the current
codebase, then define the minimum reusable foundation elements and dependency rules needed to build
remaining capabilities incrementally. Reuse the current backend/frontend layering, OpenAPI flow,
and deterministic domain model instead of introducing new frameworks or architectural abstractions.

## Technical Context

**Language/Version**: Markdown-first planning artifacts; project baseline remains Python 3.12 and TypeScript 5.x

**Primary Dependencies**: Existing repository artifacts only (README, specs, OpenAPI, tests, source tree)

**Storage**: Versioned documentation under `specs/003-readme-alignment-foundation/`

**Testing**: Evidence review against existing test suites and contracts; checklist validation for completeness

**Target Platform**: Cross-team planning and implementation handoff in current repository workflow

**Project Type**: Web application planning slice (documentation and delivery sequencing)

**Performance Goals**: Contributors identify first executable roadmap slice in under 30 minutes (SC-004)

**Constraints**: Keep planning artifacts lightweight; prefer extension of existing components/services over net-new systems

**Scale/Scope**: One alignment baseline across all major README capability areas and one reusable foundation catalog

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-research | Post-design evidence |
|---|---|---|
| Output contract | PASS | Alignment map and roadmap keep output-contract-first behavior as non-negotiable baseline for future slices. |
| Simple runtime | PASS | Foundation catalog reuses existing questionnaire + answers -> interaction + result + health model and avoids new runtime abstractions. |
| Typed UI | PASS | Plan preserves schema-driven component contracts and stable machine values as extension constraints. |
| Bounded AI | PASS | AI capabilities are tracked separately from deterministic core and must retain deterministic fallback. |
| Continuous projection | PASS | Roadmap acceptance requires preserving per-answer projection, provenance, health, and readiness recomputation. |
| Explainable health | PASS | Health and attention-item explainability is preserved as a core contract in all planned slices. |
| Stable publication | PASS | Publication remains explicit, versioned, and auditable; no planned slice introduces mutable published behavior. |

All gates pass pre-research. Re-check outcome after Phase 1 design: **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/003-readme-alignment-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── alignment-artifacts.md
└── tasks.md             # Produced by /speckit.tasks
```

### Source Code (repository root)

```text
backend/
├── src/qava/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── ports/
└── tests/

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── composables/
│   ├── router/
│   ├── stores/
│   └── views/
└── tests/

openapi/
└── qava.openapi.json

specs/
├── 001-qava-mvp/
├── 002-deterministic-runtime-hardening/
└── 003-readme-alignment-foundation/
```

**Structure Decision**: Keep architecture unchanged and plan incremental work by reusing existing
backend domain/application seams and frontend view/composable/component seams.

## Delivery Slices

### Slice 1: Alignment Baseline (P1)

- Build a README aspiration map with status: implemented, partial, missing.
- Attach evidence references and next-action notes for each partial/missing area.
- Gate: 100% aspiration coverage with traceable evidence and ownership.

### Slice 2: Foundation Catalog and Coupling Rules (P2)

- Define minimal reusable foundation elements across API, application, domain, infrastructure,
  frontend composition, and transport contracts.
- Define allowed dependency directions and prohibited coupling patterns.
- Gate: every planned enhancement can name reused elements and one explicit extension seam.

### Slice 3: Prioritized Roadmap (P3)

- Convert gaps into a sequenced roadmap of small slices tied to README outcomes.
- Each slice must list preserved behaviors, contract checks, and risk flags before implementation.
- Gate: first slice is executable without further clarification and preserves current working flow.

## Task Generation Guardrails

- Keep tasks vertical and small; prefer modifying existing modules over creating new frameworks.
- Require explicit reuse mapping in each task: which foundation element is reused, which seam is extended.
- Require a no-regression check for deterministic session flow and OpenAPI contract consistency.
- Avoid introducing new persistence models unless a README gap cannot be closed through existing ones.
- Favor contracts/tests/docs updates that strengthen traceability before adding feature breadth.

## Complexity Tracking

No constitutional violations. This plan intentionally minimizes complexity by reusing current
project structure and contracts.
