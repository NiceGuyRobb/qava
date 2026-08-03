# Research: Architecture Usage Diagram

## Decision: Use one portable Mermaid `flowchart LR` with three phase subgraphs

**Rationale**: The existing documentation establishes portable Mermaid and subgraph conventions. A left-to-right flow better fits Qava's end-to-end product story while three labeled phase subgraphs keep authoring, interview, and delivery distinct. The main path can stay solid and numbered without turning into an implementation topology diagram.

**Alternatives considered**:

- Actor swimlanes: rejected because author, respondent, client, engine, agent, persistence, and adapter lanes would obscure the essential product loop.
- Multiple diagrams: rejected because the user requested one concise view that teaches both flow and architecture.
- A deployment diagram: rejected because the feature documents conceptual responsibilities and trust boundaries, not infrastructure.

## Decision: Center the deterministic engine and make AI an optional sidecar

**Rationale**: The engine owns validation, mappings, result projection, health, readiness, and publication gates. Dashed arrows from a policy-constrained bounded agent may lead only to authoring proposals and runtime ranking or clarification. A solid deterministic eligibility-and-ordering node makes the fallback visible.

**Alternatives considered**:

- Agent placed in the primary path: rejected because it incorrectly implies that the interview depends on AI availability.
- Omit the agent: rejected because the diagram must explain the bounded judgment feature and its trust boundary.

## Decision: Put audit records in a lower persistence band

**Rationale**: Published questionnaires, session snapshots and revisions, append-only interactions, and publication attempts and receipts are supporting records. A separate band communicates auditability without presenting Qava as a full event-sourced control flow.

**Alternatives considered**:

- Connect every node to a datastore: rejected because it makes the narrative illegible.
- Omit persistence: rejected because versioning, resume, and durable publication receipts are part of the architectural story.

## Decision: Distinguish preview from publication with topology and verbs

**Rationale**: The canonical result draft and health remain inside the interview loop and are labeled side-effect-free. Delivery starts only when a user explicitly authorizes a ready revision; the publication gate precedes the output adapter, destination artifact, and receipt.

**Alternatives considered**:

- A direct arrow from result to destination: rejected because it implies continuous external writes.
- A publication gate without user authorization: rejected because the constitution requires an explicit authorized action.

## Decision: Pair the diagram with a compact legend and ordered text alternative

**Rationale**: Labels, solid-versus-dashed edges, and phase grouping must be understandable without color. Mermaid supports `accTitle` and a multi-line `accDescr { ... }` block for SVG title and description metadata. A visible five-step alternative still preserves the journey, trust boundaries, fallback, and audit model when Mermaid is unavailable or that metadata is not retained by the renderer.

**Alternatives considered**:

- Decorative color classes: rejected because they are unnecessary, can be renderer-dependent, and would make meaning depend on color.
- Long explanatory prose: rejected because it would duplicate the README rather than orient the reader.

## Verified Mermaid Constraints

- Context7 documentation for the official `/mermaid-js/mermaid` library confirms `flowchart LR`, subgraphs, labeled links, dashed labeled links, and edges to or from subgraphs.
- The implementation can use a short single-line `accTitle:` and a multi-line `accDescr { ... }` block directly after the flowchart declaration. These enhance rendered SVG accessibility but do not replace visible alternative text.
- Keep the diagram portable: avoid initialization directives, renderer-specific theme configuration, and visual meaning encoded only through color.