# Research: README Alignment Foundation

## Decision 1: Use an Evidence-Based Alignment Map as the Single Baseline

- Decision: Represent each major README aspiration area as one alignment capability record with status (`implemented`, `partial`, `missing`), evidence links, and next action.
- Rationale: This creates one shared source of truth and avoids repeated ad hoc status debates.
- Alternatives considered:
  - Freeform narrative assessment per area: rejected because status becomes hard to compare and track.
  - Immediate task-level decomposition: rejected because tasks without shared status baseline create churn.

## Decision 2: Reuse Existing Layer Seams as Foundation Elements

- Decision: Define foundations by reusing existing seams already present in the codebase (API routers, application services, domain pure functions, repositories/ports, frontend route/composable/component boundaries, OpenAPI transport boundary).
- Rationale: These seams already support running behavior and tests; reuse reduces coupling risk and onboarding cost.
- Alternatives considered:
  - Introduce a new plugin/micro-kernel system: rejected as unnecessary complexity for current scope.
  - Full architecture rewrite before roadmap: rejected because it delays value and risks breaking current flows.

## Decision 3: Lightweight Coupling Rules over New Governance Systems

- Decision: Capture coupling rules as concise artifact-level policies (allowed dependency directions, prohibited cross-layer shortcuts, required contract checks).
- Rationale: The team needs actionable guidance without adding process overhead.
- Alternatives considered:
  - Formal architecture decision platform/tooling: rejected for being heavier than current needs.
  - No coupling rules: rejected because it increases chance of local optimizations causing global regressions.

## Decision 4: Sequence Work by README Gap Closure and Risk

- Decision: Prioritize slices by value and certainty: baseline first, foundations second, roadmap third.
- Rationale: This order allows immediate clarity, then safe extensibility, then execution planning.
- Alternatives considered:
  - Start directly from roadmap slices: rejected because no stable baseline/foundation increases replanning.
  - Build foundations before baseline: rejected because foundation choices should be informed by verified gap map.

## Decision 5: Preserve Deterministic Core as Non-Negotiable

- Decision: Every future slice must keep deterministic session behavior, typed transport contracts, and OpenAPI parity checks intact.
- Rationale: README aspirations explicitly rely on these invariants; they are already implemented and should remain the stable core.
- Alternatives considered:
  - Allow temporary contract drift during roadmap execution: rejected due to high integration risk.
  - Defer deterministic checks until later slices: rejected because regressions would be detected too late.
