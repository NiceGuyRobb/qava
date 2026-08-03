# Implementation Plan: Architecture Usage Diagram

**Branch**: `005-architecture-usage-diagram` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-architecture-usage-diagram/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add one compact "How Qava Works" section to `README.md`. Its portable Mermaid flowchart tells the
author-to-respondent-to-publication story while visually separating Qava's deterministic engine,
optional bounded AI assistance, audit records, and destination adapter. A short legend and
ordered text alternative preserve the same meaning when Mermaid is unavailable.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Markdown with portable Mermaid `flowchart LR`; repository documentation convention

**Primary Dependencies**: Markdown renderer with Mermaid support; no new runtime or build dependencies

**Storage**: N/A; the feature documents existing conceptual persistence and audit stores

**Testing**: Markdown preview review, Mermaid syntax/render check, and requirements traceability review

**Target Platform**: Repository README rendered by GitHub and VS Code Markdown preview

**Project Type**: Documentation change in an existing web application repository

**Performance Goals**: A first-time reader identifies authoring, interview, and delivery phases within 60 seconds

**Constraints**: One primary Mermaid diagram; readable at normal README width; ASCII Mermaid IDs; no color-only meaning; explicit distinction between preview and publication; concise text alternative

**Scale/Scope**: One `README.md` section, one Mermaid flowchart, a short legend, and a five-step text alternative; no application or API changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Output contract - PASS**: The story starts from a declared output contract, compiles it into requirements, questions, mappings, and readiness rules, then produces a published questionnaire. The diagram makes this authoritative path explicit.
- **Simple runtime - PASS**: The central loop is `published questionnaire + accepted answer -> validate/map/recalculate -> result draft + health -> next eligible interaction`. The diagram introduces no new runtime abstractions.
- **Typed UI - PASS**: The respondent path names a client-rendered declared component and a typed answer sent for server validation; it does not assign type or mapping decisions to the client.
- **Bounded AI - PASS**: The agent appears only as dashed, policy-constrained input to compilation and interaction selection. A deterministic eligibility-and-ordering node remains a solid route to next interaction.
- **Continuous projection - PASS**: Each accepted answer flows to validation, declared mapping, canonical result draft, health, and attention items. The draft remains inside the runtime phase and is explicitly side-effect-free.
- **Explainable health - PASS**: Health is shown alongside the canonical result and attention items as a deterministic engine output; companion prose links readers to the README's detailed health rules.
- **Stable publication - PASS**: Author review produces an immutable version. A user must explicitly authorize a specific ready revision before the publication gate, adapter, destination artifact, and durable receipt.

**Post-design re-check**: PASS. The Phase 1 data model assigns every stage a stable conceptual role, the UI contract states solid and dashed edge semantics, and the quickstart validates every required trust boundary without adding a competing model.

## Project Structure

### Documentation (this feature)

```text
specs/005-architecture-usage-diagram/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Documentation (repository root)

```text
README.md                                      # Add the primary architecture-and-usage section
docs/
└── data-layout.md                             # Existing Mermaid style and persistence-boundary reference
specs/005-architecture-usage-diagram/
├── research.md                                # Diagram design decisions
├── data-model.md                              # Conceptual stages and relationships
├── contracts/
│   └── README-architecture-section.md         # Documentation/UI contract for the inserted section
└── quickstart.md                              # Preview and traceability validation guide
```

**Structure Decision**: Keep the user-facing deliverable in `README.md`, the project's existing product source of truth. The feature's supporting design records remain in its specification directory. No backend, frontend, API, or data-contract files change.

## Complexity Tracking

No constitution violations or complexity exceptions. A single README section is sufficient; separate rendered assets, diagram tooling, or implementation-specific architecture documents would make the intended orientation harder to maintain.
