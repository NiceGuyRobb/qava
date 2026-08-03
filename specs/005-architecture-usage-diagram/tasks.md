# Tasks: Architecture Usage Diagram

**Input**: Design documents from `/specs/005-architecture-usage-diagram/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [README architecture section contract](contracts/README-architecture-section.md), and [quickstart.md](quickstart.md)

**Tests**: No automated test is required because this is a documentation-only change and affects no runtime contract boundary. Perform the Mermaid-capable Markdown preview and traceability checks in [quickstart.md](quickstart.md).

**Organization**: Tasks are grouped by user story so each reader-facing documentation outcome can be implemented and reviewed independently.

## Phase 1: Setup

**Purpose**: Locate the stable README insertion point and preserve the existing documentation narrative.

- [X] T001 Confirm the `Product Thesis` to `Design Goals` insertion point and add the `## How Qava Works` section scaffold in README.md

---

## Phase 2: Foundational

**Purpose**: Establish portable Mermaid and accessibility conventions that all diagram content depends on.

- [X] T002 Add the `flowchart LR` declaration, `accTitle`, and multi-line `accDescr` metadata in the new README.md section according to specs/005-architecture-usage-diagram/contracts/README-architecture-section.md

**Checkpoint**: The README has a renderable, accessible Mermaid container ready for the story flow.

---

## Phase 3: User Story 1 - Understand the End-to-End Journey (Priority: P1) MVP

**Goal**: Let a first-time reader trace Qava from an output need through authoring, interview execution, continuous result preview, and explicit delivery.

**Independent Test**: In a Mermaid-capable preview of README.md, trace the three numbered phases from the declared output contract to the destination artifact and receipt without reading detailed sections.

### Implementation for User Story 1

- [X] T003 [US1] Add `1. Authoring` nodes and solid flow from declared output contract through compile and author review to immutable published questionnaire in README.md
- [X] T004 [US1] Add `2. Interview` nodes and the solid typed-answer loop through declared component rendering, deterministic validation and mapping, canonical result draft, health, attention items, and next eligible interaction in README.md
- [X] T005 [US1] Add `3. Delivery` nodes and the solid ready-revision path through explicit user authorization, publication gate, output adapter, destination artifact, and durable receipt in README.md

**Checkpoint**: The primary product story is fully visible and distinguishes continuous in-product preview from the explicit delivery action.

---

## Phase 4: User Story 2 - Understand System Responsibilities and Trust Boundaries (Priority: P2)

**Goal**: Make deterministic ownership, optional AI assistance, fallback behavior, and audit responsibilities legible without crowding the main narrative.

**Independent Test**: Inspect README.md and confirm the bounded agent can only propose, rank, or clarify through dashed arrows, while deterministic eligibility, validation, mappings, readiness, and authorized publication remain on solid engine-owned paths.

### Implementation for User Story 2

- [X] T006 [US2] Add the bounded-agent sidecar with dashed proposal, ranking, and clarification edges plus a solid deterministic eligibility-and-ordering fallback into next-interaction selection in README.md
- [X] T007 [US2] Add the `Persistence and audit` subgraph and recording edges for published questionnaire versions, session snapshots and revisions, append-only interactions, and publication attempts and receipts in README.md

**Checkpoint**: The architecture makes the client, engine, agent, persistence, and adapter responsibilities distinguishable without implying AI-controlled correctness or publication.

---

## Phase 5: User Story 3 - Navigate to Supporting Detail (Priority: P3)

**Goal**: Make the diagram useful when rendered and when it is not, while connecting readers to the README's detailed source sections.

**Independent Test**: Read the legend and text alternative in README.md without rendering Mermaid; verify they preserve the three phases, deterministic fallback, side-effect-free preview, publication gate, and audit record story, then follow each supporting link.

### Implementation for User Story 3

- [X] T008 [US3] Add a concise legend and companion links to the existing authoring, runtime, projection, health, publication, persistence, and safety sections in README.md
- [X] T009 [US3] Add a five-step ordered text alternative covering authoring, typed interview execution, bounded AI and deterministic fallback, inspectable preview and audit, and explicitly authorized delivery in README.md

**Checkpoint**: The orientation section remains understandable in a non-Mermaid renderer and directs readers to accurate detailed documentation.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Validate rendering, accessibility, conceptual completeness, and the absence of misleading direct paths.

- [X] T010 Verify the Mermaid source in README.md renders in VS Code Markdown Preview and follows the visual, trust-boundary, preview-versus-delivery, persistence, and text-alternative scenarios in specs/005-architecture-usage-diagram/quickstart.md
- [X] T011 Verify README.md against every required content and diagram rule in specs/005-architecture-usage-diagram/contracts/README-architecture-section.md, including no direct result-to-destination edge and no bounded-agent path to accepted answers or publication
- [X] T012 Run `git diff --check` and review the final README.md section for concise copy, ASCII Mermaid IDs, no color-only meaning, and no unrelated documentation changes

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on T001 and blocks the diagram's story content.
- **User Story 1 (Phase 3)**: Depends on T002 and delivers the MVP diagram.
- **User Story 2 (Phase 4)**: Depends on T005 because it adds architectural context around the finished story spine.
- **User Story 3 (Phase 5)**: Depends on T007 because its legend and alternative describe the completed diagram semantics.
- **Polish (Phase 6)**: Depends on T009.

### User Story Dependencies

- **US1 (P1)**: Starts after T002; no dependency on later stories.
- **US2 (P2)**: Builds on the P1 Mermaid flow because it annotates its engine and delivery boundaries.
- **US3 (P3)**: Builds on the completed diagram so its legend and text alternative exactly match the rendered semantics.

### Parallel Opportunities

No implementation tasks are marked `[P]`: each task deliberately changes the same concise README section, and serial edits keep the diagram coherent. The only parallelizable activity is a review split after T009, where one reviewer uses the rendered diagram and another checks the text alternative against `quickstart.md`.

## Implementation Strategy

### MVP First

1. Complete T001-T002 to establish a stable insertion point and portable Mermaid accessibility metadata.
2. Complete T003-T005 to deliver the readable authoring, interview, and delivery story.
3. Preview README.md and validate the US1 independent test before adding architectural detail.

### Incremental Delivery

1. Add T006-T007 to make boundaries, fallback, and audit responsibilities visible.
2. Add T008-T009 to provide reader navigation and a non-visual alternative.
3. Complete T010-T012 before review or merge.