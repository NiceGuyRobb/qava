# Feature Specification: Architecture Usage Diagram

**Feature Branch**: `005-architecture-usage-diagram`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Look at what we have and create an architecture diagram that can be used to show how to use this system as much as it is explaining the design of the system."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the End-to-End Journey (Priority: P1)

A prospective author, respondent, or stakeholder views one architecture diagram and understands how an output need becomes a published questionnaire, how answers progressively produce a result, and how a ready result is explicitly published.

**Why this priority**: The diagram's primary value is to communicate the complete product loop without requiring the reader to assemble it from separate sections of the README.

**Independent Test**: A reader who has not used Qava can trace the numbered authoring, interviewing, and publication stages from input through outcome using the diagram alone.

**Acceptance Scenarios**:

1. **Given** a reader has an output they need to produce, **When** they follow the diagram, **Then** they can identify the authoring inputs, the review-and-publication decision, and the resulting immutable questionnaire.
2. **Given** a reader begins an interview, **When** they follow the runtime loop, **Then** they can identify where a typed answer is captured, validated, projected into the result draft, and used to select the next interaction.
3. **Given** a result becomes eligible for delivery, **When** the reader follows the publication path, **Then** they can distinguish continuous preview from the separate explicit publication action and receipt.

---

### User Story 2 - Understand System Responsibilities and Trust Boundaries (Priority: P2)

A technical stakeholder uses the same diagram to see which responsibilities belong to the author, respondent, client, deterministic engine, bounded agent, persistence, and output adapter.

**Why this priority**: The diagram should explain Qava's safety model rather than accidentally imply that AI or a client can control validation, mappings, or publication.

**Independent Test**: A reviewer can point to each principal responsibility and identify that the agent only proposes or ranks within policy while the engine validates and the user authorizes publication.

**Acceptance Scenarios**:

1. **Given** the diagram displays the bounded agent, **When** a reader inspects its connections, **Then** the reader sees that it supplies proposals, ranking, or clarification assistance rather than accepted answers or external side effects.
2. **Given** the diagram displays answer submission and result publication, **When** a reader traces either path, **Then** validation, mapping, readiness, and explicit authorization are visibly enforced by the system.

---

### User Story 3 - Navigate to Supporting Detail (Priority: P3)

A README reader uses the diagram as an orientation point and can move to the surrounding documentation for precise component, health, safety, and persistence details.

**Why this priority**: A diagram must remain legible while still directing readers to the existing detailed source of truth.

**Independent Test**: A reader can identify the diagram's concise legend and find adjacent references for the product loop, health, publication, safety, and audit explanations.

**Acceptance Scenarios**:

1. **Given** a reader needs more detail about a labeled stage, **When** they use the diagram's companion text, **Then** they are directed to the existing documentation section that expands that stage.

### Edge Cases

- A renderer cannot display the diagram format: the documentation must retain a concise text alternative that preserves the three phases and key trust boundaries.
- The diagram becomes visually dense as new adapters or renderers are added: the primary path remains limited to the canonical result and explicit publication, while optional ecosystem extensions remain clearly secondary.
- Agent availability is misread as a dependency: the diagram must state or visually show deterministic eligibility and ordering as the fallback path.
- A reader mistakes result preview for an external write: the diagram must distinguish side-effect-free projection from the explicitly authorized adapter path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Documentation MUST include one architecture diagram that presents the end-to-end path from a declared output contract through authoring, interview execution, result projection, and destination artifact.
- **FR-002**: The diagram MUST make author actions, respondent actions, and explicit publication authorization distinguishable from system-managed processing.
- **FR-003**: The diagram MUST show authoring as a reviewable process that produces an immutable, versioned published questionnaire before runtime execution begins.
- **FR-004**: The diagram MUST depict the runtime loop as typed answer capture, deterministic validation and mapping, canonical result and health update, and next-interaction selection.
- **FR-005**: The diagram MUST show continuous result preview as side-effect-free and publication as a separately authorized path through an output adapter that records a receipt.
- **FR-006**: The diagram MUST identify the bounded agent as optional assistance limited to declared policy, with deterministic execution remaining available when AI assistance fails or is unavailable.
- **FR-007**: The diagram MUST visibly separate inputs, engine responsibilities, persisted records, and external destinations so readers can understand their relationships without consulting implementation code.
- **FR-008**: Documentation MUST provide a concise legend or companion explanation that defines visual conventions and links the diagram stages to the detailed README sections.
- **FR-009**: The diagram and companion text MUST be readable in the repository's standard documentation preview and retain a text alternative for readers unable to render the diagram.

### Constitution Alignment *(mandatory)*

- **Output Contract Impact**: The diagram begins with the output contract as the authoritative input, shows its compilation into declared requirements, questions, mappings, and readiness rules, and never presents questions or AI as competing sources of truth.
- **Typed Interaction Impact**: The runtime path shows the client rendering a declared component, collecting a typed value, and sending it to the engine for validation before it can affect the canonical result.
- **AI Policy Boundary**: The diagram limits agent participation to authoring proposals, interaction ranking, and bounded clarification. It makes validation, accepted values, identifiers, mappings, and publication deterministic, and shows a fallback path without AI.
- **Projection and Health**: Every accepted answer leads to a recalculated canonical draft, provenance-aware health assessment, attention items, and the next eligible interaction; preview remains inspectable at each revision.
- **Publication and Stability**: The diagram distinguishes draft authoring from immutable published versions and portrays publication as an explicit, readiness-gated adapter action with an auditable receipt.

### Key Entities *(include if feature involves data)*

- **Architecture usage diagram**: A visual map that combines the product journey, system responsibilities, boundaries, and primary data flow.
- **Diagram stage**: A labeled point in the authoring, runtime, or delivery path that maps to existing Qava documentation and responsibilities.
- **Text alternative**: A concise ordered explanation of the same stages and safeguards for non-visual or unsupported rendering contexts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time reader can identify the three major phases (authoring, interview, and delivery) and their entry and exit artifacts within 60 seconds of viewing the diagram.
- **SC-002**: In a documentation review, 100% of the required concepts are traceable in the diagram or its companion explanation: output contract, immutable questionnaire, typed answer, validation, canonical result, health, bounded agent, deterministic fallback, explicit publication, adapter, and receipt.
- **SC-003**: At least 4 out of 5 reviewers can correctly explain that result preview does not publish externally and that publication requires an explicit authorized action after a single reading.
- **SC-004**: The diagram remains usable at standard documentation preview width without overlapping labels, and its text alternative permits the same three-phase journey to be followed without visual rendering.

## Assumptions

- The architecture diagram will be maintained with the README because that document is the existing product and architectural source of truth.
- Mermaid is an acceptable documentation diagram format because the repository already uses Mermaid in existing documentation.
- The first diagram focuses on the MVP canonical JSON result and JSON document adapter; additional adapters and renderers are represented as optional extensions rather than equal-weight primary paths.
- The diagram will describe current intended architecture and user flow, not implementation-specific modules, endpoints, or deployment topology.