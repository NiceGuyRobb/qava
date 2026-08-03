# Data Model: Deterministic Runtime Hardening

## Changed Entities

### SessionRecord (extended)

The persisted session snapshot gains two optional state fields stored as JSON columns on the
existing `sessions` table. No existing fields change. Both fields are set atomically with
`answers_json` inside the revision-checked `UPDATE … WHERE revision = :expected_revision`.

| Field | Type | Semantics |
|---|---|---|
| `skip_dispositions` | `dict[str, SkipDisposition]` | Keyed by question ID. Present entry means that optional question was permissibly skipped at the recorded revision. Removed when the question is answered; evaluation clears its selective effect when the question becomes inapplicable. |
| `navigation_focus` | `NavigationFocus \| None` | Single target persisted after a valid navigation mutation. Honored by evaluation before ordinary deterministic ordering. Cleared when the target is answered, permissibly skipped, resolved, or inapplicable. |

```
SessionRecord
├── session_id: SessionId
├── questionnaire_id: QuestionnaireId
├── questionnaire_version: int
├── revision: int                    # compare-and-swap key
├── status: SessionStatus
├── active_topic_id: str | None
├── answers: dict[str, Any]
├── generated_interactions: list
├── skip_dispositions: dict[str, SkipDisposition]   # NEW
├── navigation_focus: NavigationFocus | None         # NEW
├── created_by: str
├── created_at: datetime
└── updated_at: datetime
```

### SkipDisposition (new embedded record)

Stored inline within `skip_dispositions` JSON; no separate table.

| Field | Type | Description |
|---|---|---|
| `question_id` | `str` | The skipped question. |
| `accepted_revision` | `int` | Revision at which the skip was accepted. |
| `actor_id` | `str` | Actor who submitted the skip. |
| `skipped_at` | `datetime` | UTC timestamp of acceptance. |

### NavigationFocus (new embedded record)

Stored inline as `navigation_focus` JSON on the session row; one entry maximum.

| Field | Type | Description |
|---|---|---|
| `question_id` | `str` | Currently targeted question. |
| `output_need_id` | `str \| None` | Output need that triggered navigation, if any. |
| `topic_id` | `str \| None` | Topic/section that triggered navigation, if any. |
| `accepted_revision` | `int` | Revision at which navigation was accepted. |
| `actor_id` | `str` | Actor who submitted navigation. |

---

## New Domain Value Objects

### SessionEvaluation (immutable, not persisted)

Returned by `evaluate_session(questionnaire, session)`. All downstream session view fields derive
from this single computation.

| Field | Type | Description |
|---|---|---|
| `applicable_question_ids` | `frozenset[str]` | Questions whose applicability conditions are satisfied given current answers. |
| `active_answer_ids` | `frozenset[str]` | Questions in `applicable_question_ids` that also have an accepted answer. |
| `active_skip_ids` | `frozenset[str]` | Questions in `applicable_question_ids` that have a skip disposition and no answer. |
| `current_interaction` | `dict \| None` | Navigation-focus question if still eligible; otherwise deterministic next eligible unanswered/unskipped question. |
| `projection` | `ProjectionResult` | Result data, provenance, changed paths; computed over active answers only. |
| `unresolved_needs` | `list[dict]` | Output needs with no active answer from any question serving them. |
| `progress` | `Progress` | Required needs satisfied vs total required; derived from unresolved needs. |
| `health` | `HealthAssessmentRecord` | Five dimensions, readiness, attention; computed over active answers and output needs. |
| `permitted_actions` | `list[str]` | Deterministic action set: `answer`, `skip` (only if current is optional and not already skipped), `navigate`, `save_and_exit`, `delete`, `preview_publication`/`publish` if ready. |

### Progress (inline, not persisted)

| Field | Type |
|---|---|
| `satisfied_required` | `int` |
| `total_required` | `int` |

---

## API Transport Models (new `api/schemas.py`)

Transport models are separate from domain records. Routers convert between them at the boundary.

### Request Models

| Model | Purpose |
|---|---|
| `CreateDraftRequest` | `id: str`, `title: str`, `description: str \| None`, `output_contract: dict` |
| `UpdateDraftRequest` | `operations: list[DraftOperation]` |
| `PublishDraftRequest` | No body; revision enforcement via header |
| `CreateSessionRequest` | `questionnaire_id: str`, `questionnaire_version: int` |
| `SubmitAnswerRequest` | `interaction_id: str`, `value: Any`, `expected_revision: int` |
| `SkipInteractionRequest` | `interaction_id: str`, `expected_revision: int` |
| `NavigateRequest` | `expected_revision: int`, `output_need_id: str \| None`, `section_id: str \| None` |

### Response Models

| Model | Source |
|---|---|
| `QuestionnaireDraftResponse` | Draft state after create/update |
| `PublishedQuestionnaireResponse` | Immutable questionnaire receipt |
| `SessionView` | Authoritative session evaluation (all reads and mutations) |

### Shared Problem Response

`ProblemDetail` (`type`, `title`, `detail`, `status`, `instance?`) is already defined in
`domain/models.py`; routers declare it for 404, 409, and 422 responses.

---

## Schema Migration

A second Alembic revision adds the two JSON columns to `sessions`. The revision is additive and
backward-compatible because both columns default to their empty serialized forms, and existing
rows are read as having no skip dispositions and no navigation focus.

```sql
-- 0002_session_disposition_focus
ALTER TABLE sessions ADD COLUMN skip_dispositions_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE sessions ADD COLUMN navigation_focus_json TEXT;
```

Revision chain: `0001_initial → 0002_session_disposition_focus`

---

## Validation Rules

| Constraint | Where enforced |
|---|---|
| Skip permitted only for optional interactions | Pre-mutation evaluation check in `InterviewingService` |
| Skip rejected if already present for the current applicable question | Pre-mutation check against `active_skip_ids` |
| Navigation target must be in `unresolved_needs` | Pre-mutation check against evaluation |
| Navigation target must be in `applicable_question_ids` | Pre-mutation check against evaluation |
| All mutations check `session.revision == expected_revision` | `update_with_revision` SQL compare-and-swap |
| Stale write returns 409 | `StaleRevisionError` mapped in router |
| Skip of required interaction returns 422 | `ValueError` mapped in router |
| Navigate to resolved/inapplicable need returns 422 | `ValueError` mapped in router |

---

## State Transitions

### Skip Disposition

```
Eligible optional question selected
  -> respondent submits skip
  -> evaluation: action "skip" in permitted_actions
  -> revision-checked update: add disposition, answers unchanged
  -> evaluator on next read: question in active_skip_ids -> excluded from current_interaction
  -> IF question becomes inapplicable: disposition has no selective effect
  -> IF question becomes applicable again: remains skipped unless answered or disposition cleared
  -> IF respondent answers the question: disposition removed from session row
```

### Navigation Focus

```
Respondent requests navigation to output_need_id or section_id
  -> evaluation: target in unresolved_needs AND applicable_question_ids
  -> revision-checked update: set navigation_focus to {question_id, context, revision, actor}
  -> evaluator on next read: navigation_focus question still eligible -> becomes current_interaction
  -> IF target answered: focus cleared
  -> IF target skipped: focus cleared
  -> IF target becomes inapplicable or resolved: focus cleared by evaluator (not persisted)
```

---

## Preserved Existing Entities (unchanged)

- `PublishedQuestionnaireRecord`: immutable after publication; questionnaire questions, output
  needs, health policy, and assistance policy are unchanged.
- `RuntimeInteractionRecord`: append-only audit log; not queried for current state.
- `DraftRepository`: existing upsert/get/delete protocol; deletion path is now exercised.
- Projection, health, selection, condition domain functions: inputs now filtered through
  `SessionEvaluation.active_answer_ids` but function signatures are unchanged.
