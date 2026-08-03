# Qava README ↔ Implementation Gap Analysis

**Created**: 2026-07-26
**Purpose**: Provide a verified baseline of what the README aspires to versus what is built today, to serve as structured input for the `003-readme-alignment-foundation` spec.
**Scope**: Backend (`backend/src/qava`), frontend (`frontend/src`), and prior specs (`001-qava-mvp`, `002-deterministic-runtime-hardening`).
**Method**: Full README read plus a code-level inventory of both stacks. Status is classified as **Implemented**, **Partial**, or **Missing** with concrete evidence.

---

## 1. Executive Summary

The **deterministic core loop is real and solid**: contract → questionnaire → session → typed answers → continuous JSON projection → explainable health. A generic client renders backend-supplied component specs with no questionnaire-specific logic. This satisfies most of README **Phase 1** and much of the deterministic surface of **Phase 3**.

The **three biggest gaps** between README aspiration and current state are:

1. **No AI/agent layer at all** (README Phase 2). Every "agentic" capability — authoring proposals, adaptive next-question ranking, clarifications, extraction — is absent. Only protocol stubs and a disabled policy exist.
2. **Publication is not wired end to end** (README Phase 3 / MVP acceptance). Records, tables, and schemas exist, but there is no `POST /publications` endpoint, no adapter registry, no JSON-document adapter, no preview/validate, and no receipts.
3. **No self-hosted authoring / meta-questionnaire and no authoring UI** (README "Administration" + Phase 3). Authoring exists only as an API; there is no builder, no raw-JSON edit path, no publication UI, and no meta-questionnaire bootstrap.

Two secondary gaps: **collections and dynamic option sources are only partially implemented**, and **two renderer components (money, date/datetime) exist but are unmapped** in the frontend registry.

---

## 2. Aspiration → Status Map

Legend: ✅ Implemented · ⚠️ Partial · ❌ Missing

| # | README Aspiration Area | README Phase | Backend | Frontend | Overall |
|---|---|---|---|---|---|
| A1 | Output contract as source of truth (JSON Schema → output needs) | 1 | ✅ | n/a | ✅ |
| A2 | Questionnaire authoring & compilation (draft → immutable published version) | 1 | ✅ | ❌ (no UI) | ⚠️ |
| A3 | Author confirmation / override of ambiguous decisions | 1 | ⚠️ (no explicit confirm workflow) | ❌ | ⚠️ |
| A4 | Questions, answer schemas, stable choice IDs, direct/compose mappings | 1 | ✅ | ✅ | ✅ |
| A5 | Applicability conditions (`equals` / `contains` / `exists`) | 1 | ✅ | ⚠️ (backend-driven only) | ✅ |
| A6 | Automatic UI component selection (deterministic inference + catalog) | 1 | ✅ | ✅ | ✅ |
| A7 | Collections (`repeating_group`) | 1 | ⚠️ | ✅ (flat only) | ⚠️ |
| A8 | Dynamic option sources (named system provider) | 1 | ❌ | ⚠️ (static/enum only) | ❌ |
| A9 | Sessions, typed answers, resume, answer editing | 1 | ✅ | ✅ | ✅ |
| A10 | Continuous canonical JSON projection + provenance | 1 | ✅ | ✅ | ✅ |
| A11 | Deterministic next-question selection + fallback ordering | 1/2 | ✅ | ✅ | ✅ |
| A12 | Skip / navigation semantics | 1/2 | ✅ | ✅ | ✅ |
| A13 | Explainable health (5 dimensions + headline score + attention items) | 3 | ⚠️ (heuristic dimensions) | ✅ | ⚠️ |
| A14 | Optimistic concurrency (stale-write rejection) | 1 | ✅ | ✅ | ✅ |
| A15 | Interaction audit log (append-only) | 1 | ✅ | n/a | ✅ |
| A16 | **Authoring agent proposals** (questions, mappings, components) | 2 | ❌ | ❌ | ❌ |
| A17 | **Adaptive agent next-question ranking** | 2 | ❌ | ❌ | ❌ |
| A18 | **Bounded runtime clarifications** | 2 | ❌ | ❌ | ❌ |
| A19 | **Structured extraction proposals** (free text → validated value) | 2 | ❌ | ❌ | ❌ |
| A20 | Agent audit metadata (model, policy, evidence) | 2 | ⚠️ (tables only) | ❌ | ❌ |
| A21 | **Output adapters + explicit publication + receipts + idempotency** | 3 | ⚠️ (records only, no service/endpoint) | ❌ | ❌ |
| A22 | JSON document adapter | 3 | ❌ | ❌ | ❌ |
| A23 | **Self-hosted authoring / meta-questionnaire + registry adapter** | 3 | ❌ | ❌ | ❌ |
| A24 | Raw questionnaire JSON edit escape hatch | 3 | ⚠️ (API accepts JSON) | ❌ (no UI) | ⚠️ |
| A25 | Pluggable renderers (mobile/terminal/voice) | 4 | n/a (contract pluggable) | ❌ (one web renderer) | ⚠️ |
| A26 | Additional adapters (DB, CSV, Excel, message bus, HTTP) | 4 | ❌ | ❌ | ❌ |

---

## 3. Detailed Findings

### 3.1 Implemented and trustworthy (protect these)

These are the stable foundations the roadmap should build on, not rewrite.

- **Output contract handling** — `domain/definition.py` (`derive_output_needs`, `validate_publication`); contract stored immutably in `application/authoring.py`. Output needs carry `id`, `target` (JSON pointer), `value_schema`, `required`, `criticality`.
- **Authoring & compilation (API)** — `application/authoring.py` (`create_draft`, `update_draft`, `publish_draft`), `infrastructure/contracts/definition_pack.py`, router `api/routers/questionnaires.py`. Published questionnaires are immutable and monotonically versioned.
- **Questions / choices / mappings / conditions** — `domain/answers.py` (validation + stable choice IDs), `domain/projection.py` (`direct` and `compose` modes with provenance), `domain/conditions.py` (`equals`, `contains`, `exists`, nested paths, `any`).
- **Deterministic component inference** — `domain/components.py` (`infer_component`, `is_component_compatible`), catalog at `data/components/catalog.v1.json`, validated by `infrastructure/contracts/registry.py`.
- **Runtime interview** — `application/interviewing.py`, unified evaluation in `domain/evaluation.py`, selection in `domain/selection.py`. Sessions, answers, skip, navigation, resume all work.
- **Continuous projection** — `domain/projection.py` returns `data`, `provenance`, `changed_paths`, `inactive_question_ids`; recomputed on every read/mutation.
- **Persistence & optimistic concurrency** — `infrastructure/database/repositories.py` (published questionnaires, sessions, interactions, drafts); revision-guarded updates raise `StaleRevisionError`.
- **Frontend generic renderer** — `components/interview/SemanticRenderer.vue` + `components/renderers/registry.ts` with fallback logic; interview flow in `views/InterviewView.vue`, `QuestionStage.vue`, `SessionRail.vue`; health display in `components/health/HealthPanel.vue`; result in `components/result/ResultWorkspace.vue` + `JsonTree.vue`.
- **API client** — `api/client.ts` wires session create/get/answer/skip/navigate and draft create/publish; RFC 7807 problem handling.

### 3.2 Partial — foundations exist but incomplete

- **A3 Author confirmation/override**: Drafts recompile on change, but there is no explicit "unresolved decision → confirm/override/reject" workflow surfaced by the API or any UI. README treats author confirmation of ambiguous UI choices as a first-class MVP behavior.
- **A7 Collections**: `repeatable_group` is recognized (`_answer_schema` → array) with `max_collection_depth`/`max_collection_items` limits, and the frontend `RepeatableGroup.vue` supports add/remove of flat items. **Missing**: nested repeating groups, per-item applicability ("if any item has X"), and per-item compose mapping — all needed for the README's self-hosting story.
- **A13 Health dimensions**: All five dimensions and the weighted headline score exist (`domain/health.py`), and attention items surface blocking issues. **However** confidence, consistency, and specificity are placeholder heuristics (e.g., consistency is hard-coded to 100). README expects inspectable, rule-based scoring per dimension, and validity may include an adapter dry run.
- **A20 Agent audit metadata**: `assistance_proposals` table and `AssistanceProposalRepository` protocol exist but are never called; no model/policy/evidence is captured because no agent runs.
- **A21 Publication**: `PublicationRecord` model and `publication_attempts` table exist with status/idempotency/receipt columns, plus a `PublicationAttemptRepository` protocol — but **zero service code and no endpoint** invoke them.
- **A24 Raw JSON edit**: The authoring API accepts questionnaire JSON, so a raw path is technically reachable, but there is no UI and no explicit "same publication gate for both routes" convergence proven.
- **A25 Pluggable renderers**: The component-spec contract is renderer-neutral by design, but only one web renderer exists; **money_input** and **date/datetime** components exist as `.vue` files (`MoneyField.vue`, `DateTimeField.vue`) but are **not mapped** in `registry.ts`, so they cannot be selected.

### 3.3 Missing — no meaningful implementation

- **A16–A19 Entire AI/agent layer (README Phase 2)**: No LLM integration anywhere. `config.py` `assistance_mode` is `"disabled"` (only `disabled`/`fixture`). No authoring proposals, no adaptive ranking, no clarifications, no extraction. Selection is fixed priority order. This is the single largest aspiration gap.
- **A22 JSON document adapter**: Not implemented; `"json-document"` appears only as a string in the client.
- **A23 Self-hosted authoring / meta-questionnaire + registry adapter (README "Administration")**: No meta output contract, no bootstrap questionnaire, no registry adapter, no authoring/publication UI (`frontend` has no `/authoring/*`, `/drafts/*`, or `/publications/*` routes).
- **A26 Adapter/renderer ecosystem (README Phase 4)**: Explicitly deferred; not started (expected).

---

## 4. Gaps Grouped by README Delivery Phase

| Phase | Aspiration | Reality | Remaining gap |
|---|---|---|---|
| **Phase 1 — Contract to Working Questionnaire** | Author publishes contract, respondent answers via generated UI, JSON updates each answer | Largely done | Author confirmation workflow (A3); collections depth (A7); dynamic option sources (A8); unmapped money/date components (A25) |
| **Phase 2 — Bounded Agent** | AI improves authoring & interview without controlling schemas/values/publication | Not started | Entire layer: authoring proposals, ranking, clarifications, extraction, deterministic fallback wiring, agent audit (A16–A20) |
| **Phase 3 — Health & Publication** | Explainable health + safe explicit publication + self-hosting | Health present (heuristic); publication & self-hosting absent | Rule-based health dimensions (A13); publication endpoint + JSON adapter + receipts + idempotency (A21, A22); meta-questionnaire + registry adapter + authoring/publication UI (A23) |
| **Phase 4 — Ecosystem** | More adapters & renderers | Not started (expected) | Deferred; out of near-term scope (A26, most of A25) |

---

## 5. Loosely Coupled Foundation Elements (for the 003 spec)

These are the stable seams the roadmap should compose against, matching the spec's "minimal foundational element catalog" goal.

| Foundation element | Location | Role | Extension seam |
|---|---|---|---|
| **Output-need derivation** | `domain/definition.py` | Contract → addressable needs | Add derived/agent-satisfied need modes later |
| **Answer validation** | `domain/answers.py` | Enforce schema + stable choice IDs | Gate for agent-extracted proposals |
| **Component resolution** | `domain/components.py` + catalog | Deterministic UI selection | Insert agent recommendation between deterministic + fallback |
| **Session evaluation** | `domain/evaluation.py` | Single source of session view | Insert agent ranking over deterministic eligible set |
| **Projection** | `domain/projection.py` | Canonical result + provenance | Add compose modes for collections |
| **Health assessment** | `domain/health.py` | Dimensions + score + attention | Replace heuristic dimensions with rule-based scorers; add adapter dry-run to validity |
| **Repository protocols** | `ports/repositories.py` | Storage seam | Publication + assistance repos already stubbed, ready to wire |
| **Semantic renderer** | `frontend/.../SemanticRenderer.vue` + `registry.ts` | Renderer-neutral UI seam | Register money/date; add async option loading |

**Key coupling rule already respected**: the client contains no questionnaire-specific logic; all decisions flow from the backend session view. Any new capability must preserve this so alternate renderers (A25) stay possible.

---

## 6. Recommended Prioritized Sequence (input to roadmap slices)

Ordered by value-per-effort while preserving the working deterministic core.

1. **Close cheap Phase 1 gaps** (low risk, high polish):
   - Map `MoneyField` and `DateTimeField` in `registry.ts` (A25).
   - Wire dynamic option sources (A8) and per-item collection compose (A7) — both are prerequisites for self-hosting.
2. **Publication end to end** (A21 + A22): implement JSON document adapter, `POST /publications`, preview/validate, receipts, idempotency, and a minimal publication UI. Records/tables already exist.
3. **Rule-based health** (A13): replace heuristic confidence/consistency/specificity with inspectable rules; add optional adapter validation dry run to validity.
4. **Author confirmation workflow** (A3) + minimal authoring UI / raw JSON edit path (A24): unlocks self-service authoring.
5. **Self-hosted meta-questionnaire + registry adapter** (A23): depends on collections (A7), dynamic options (A8), authoring UI (A3/A24), and publication (A21).
6. **Bounded agent layer** (A16–A20): introduce behind the existing disabled policy and stubbed repositories, always with deterministic fallback. Sequence: component recommendation → next-question ranking → authoring proposals → bounded clarification → extraction.
7. **Ecosystem** (A26, broader A25): defer per README Phase 4.

---

## 7. Traceability Notes

- Prior spec **`001-qava-mvp`** targets the full MVP loop; this analysis shows Phase 1 and deterministic Phase 3 (health) are largely delivered, while publication, self-hosting, and the agent layer remain open.
- Prior spec **`002-deterministic-runtime-hardening`** unified evaluation, skip/navigation, and the API contract — consistent with the "Implemented and trustworthy" findings in §3.1.
- The **`003-readme-alignment-foundation`** spec (this artifact's consumer) can adopt §2 as its Alignment Capability Records, §5 as its Foundation Element Definitions and Coupling Rules, and §6 as its Roadmap Slices.

---

## 8. Evidence Confidence

- Backend and frontend inventories are code-verified against the current tree; file paths are authoritative, and specific line numbers are approximate.
- "Missing" classifications reflect absence of call sites / endpoints / UI, not merely absence of schema — e.g., publication and assistance have storage scaffolding but no runtime behavior.
