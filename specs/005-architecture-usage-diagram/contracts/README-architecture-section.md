# README Architecture Section Contract

## Placement

Insert a new `## How Qava Works` section after the README's introductory product thesis and before detailed design goals. It serves as an orientation map; existing detailed sections remain the source of truth.

## Required Content

1. One Mermaid `flowchart LR` with three explicitly labeled subgraphs:
   - `1. Authoring` from declared output contract through author review to an immutable, versioned published questionnaire.
   - `2. Interview` from client rendering and respondent typed answer through deterministic validation, mapping, canonical result draft, health, and next eligible interaction.
   - `3. Delivery` from a selected ready revision through explicit user authorization, publication gate, adapter, destination artifact, and durable receipt.
2. A bounded agent node with dashed labeled arrows only to authoring proposals and interaction ranking or clarification.
3. A deterministic eligibility-and-ordering fallback node with a solid arrow into next-interaction selection.
4. A `Persistence and audit` subgraph that records published questionnaires, session snapshots and revisions, append-only interactions, and publication attempts and receipts.
5. A concise legend defining solid arrows as required or deterministic flow and dashed arrows as optional, policy-constrained assistance.
6. A five-step ordered text alternative covering the same three phases, fallback, side-effect-free preview, and audit behavior.

## Diagram Rules

- Use ASCII node IDs and short visible labels; use `<br/>` only for a short second line.
- Put a single-line `accTitle:` and concise multi-line `accDescr { ... }` block immediately after `flowchart LR`. Treat this as a progressive accessibility enhancement; the visible ordered text alternative remains required.
- Use solid arrows for the product/data flow and a single dashed-arrow meaning for optional assistance.
- Do not use color, custom Mermaid initialization, renderer-specific directives, or implementation-module names to convey required meaning.
- Keep the primary delivery path generic as `Output adapter` to `Destination artifact`; state that the MVP's canonical result is typed JSON in companion prose.
- Do not route the agent to answer acceptance, mappings, publication gates, adapters, destinations, or receipts.
- Do not allow a direct result-to-destination arrow; delivery must visibly require explicit authorization and a publication gate.

## Reader Links

Companion prose should point readers to the README sections covering authoring and compilation, runtime interview, continuous result projection, result health, output adapters and publication, persistence and audit, and safety and trust boundaries.