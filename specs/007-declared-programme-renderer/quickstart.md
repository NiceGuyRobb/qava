# Quickstart: Validate Declared Programme Renderer

## Prerequisites

- Use a fresh published questionnaire version containing the `declared_programme` contract in
  [contracts/declared-programme.md](contracts/declared-programme.md).
- Start the local backend and frontend from the repository root:

```powershell
uv run --project backend uvicorn qava.main:app --host 127.0.0.1 --port 8000

Set-Location frontend
npm run dev
```

## Focused Checks

```powershell
Set-Location frontend
npm test -- SemanticRenderer.spec.ts
npm run typecheck

Set-Location ..
uv run --project backend pytest backend/tests/unit/test_definition.py -q
uv run --project backend pytest backend/tests/unit/test_definition_pack.py -q
uv run --project backend pytest backend/tests/integration/test_authoring_workflow.py -q
uv run --project backend pytest backend/tests/integration/test_interview_workflow.py -q
uv run --project backend pytest backend/tests/contract/test_data_contracts.py -q
```

Expected: a valid declaration emits stable item/status/detail values with no textarea; malformed
declarations block guided and raw publication; duplicate selected item IDs are rejected; an
accepted answer projects unchanged at its existing direct target.

## Manual Browser Scenario

1. Open a fresh session's `/sessions/{sessionId}` route for the new published version.
2. Reach the declared programme question and verify it renders group labels, item labels, and only
   declared status controls; there is no Advanced JSON input.
3. Select statuses for items in two groups and enter an optional declared detail for one item.
4. Submit the answer and confirm the session revision increments.
5. Open the result preview and confirm the mapped object contains the stable `item_id`, `status`,
   and detail values described in [data-model.md](data-model.md), not display labels.
6. Confirm the next eligible interaction and health refresh normally.
7. Validate an intentionally malformed draft declaration through guided and raw authoring; confirm
   both show a specific issue and refuse publication.
8. Open an existing session from the previous questionnaire version and confirm its session view
   and answers are unchanged.