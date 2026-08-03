# Quickstart: Validate the Architecture Usage Diagram

## Prerequisites

- A Markdown preview that supports Mermaid, such as VS Code Markdown Preview or GitHub rendering.
- The implementation follows [README Architecture Section Contract](contracts/README-architecture-section.md).

## Validation Scenarios

### 1. Read the product story

1. Open `README.md` in a Mermaid-capable preview.
2. Find `How Qava Works`.
3. Trace the numbered authoring, interview, and delivery phases from the declared output contract to the destination artifact.

**Expected outcome**: The reader can name the output contract, immutable published questionnaire, typed answer, canonical result draft, health, explicit publication, adapter, and receipt without reading the detailed sections.

### 2. Check trust boundaries

1. Trace every connection from the bounded agent.
2. Verify the agent only has dashed proposal, ranking, or clarification paths.
3. Verify deterministic eligibility and ordering feed next-interaction selection independently.
4. Verify validation and mapping occur in the deterministic runtime, and publication begins only after user authorization and the publication gate.

**Expected outcome**: AI assistance is visibly optional and cannot accept values, mutate a published questionnaire, or perform external publication.

### 3. Distinguish preview from delivery

1. Follow the answer loop to the canonical result draft, health, and attention items.
2. Confirm that this loop returns to the next eligible interaction.
3. Follow delivery separately from a ready revision through explicit authorization, gate, adapter, destination, and receipt.

**Expected outcome**: The diagram contains no direct result-to-destination flow and clearly presents preview as side-effect-free.

### 4. Check persistence and accessibility

1. Confirm the persistence band names immutable questionnaire versions, session snapshots and revisions, append-only interactions, and publication records.
2. Disable or ignore Mermaid rendering and read the ordered text alternative.
3. Confirm the alternative preserves the same authoring, interview, fallback, preview, publication, and audit story.

**Expected outcome**: The architecture remains understandable without color or Mermaid rendering.