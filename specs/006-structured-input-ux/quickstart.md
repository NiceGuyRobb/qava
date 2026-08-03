# Quickstart: Validate Structured Input UX

## Focused Checks

```powershell
Set-Location frontend
npm run test:unit -- SemanticRenderer.spec.ts
npm run typecheck

Set-Location ..
uv run --project backend pytest backend/tests/unit/test_definition.py -q
uv run --project backend pytest backend/tests/integration/test_authoring_workflow.py -q
uv run --project backend pytest backend/tests/contract/test_data_contracts.py -q
```

Expected: nested multi-select emits declared values; measurement emits the declared value/unit
object; complete forms render no textarea; unconstrained answers retain advanced JSON; incompatible
declarations block raw and guided publication.

## Browser Smoke

1. Open a real `/sessions/{sessionId}` route for a newly published custom-home version.
2. Complete `household-members`, including multiple needs, without seeing JSON.
3. Complete `home-structure`, including ceiling preferences and target area/unit.
4. Confirm the result preview updates after each accepted answer.
5. Verify an unconstrained structured test question labels JSON entry as advanced.
6. Verify an unsupported nested declaration shows a specific draft issue and blocks publication.