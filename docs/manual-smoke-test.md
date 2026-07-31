# Manual Smoke Test (Backend + Frontend)

This app intentionally redirects `/` to `/sessions`, and that route is a placeholder shell.
To test the interview flow, open a real session route: `/sessions/{sessionId}`.

## Prerequisites

- Backend dependencies installed (`uv sync --project backend`)
- Frontend dependencies installed (`npm install` in `frontend`)

## 1) Start backend

From repo root:

    uv run --project backend uvicorn qava.main:app --host 127.0.0.1 --port 8000

If port 8000 is already in use, kill the existing PID first.

## 2) Start frontend

In a second terminal:

    cd frontend
    npm run dev

Open:

    http://127.0.0.1:5173

## 3) Create a test questionnaire + session (PowerShell)

In a third terminal from repo root, run this script to create a draft, add one question,
publish, create a session, and print the session URL.

    $api = "http://127.0.0.1:8000/api/v1"
    $author = @{ "X-Qava-Identity" = '{"actor_id":"manual-author","roles":["author"]}' }
    $resp = @{ "X-Qava-Identity" = '{"actor_id":"manual-respondent","roles":["respondent"]}' }
    $id = "manual-$(Get-Date -Format yyyyMMddHHmmss)"

    $draftBody = @{
      id = $id
      title = "Manual Smoke"
      output_contract = @{
        type = "object"
        properties = @{ project_name = @{ type = "string" } }
        required = @("project_name")
      }
    } | ConvertTo-Json -Depth 10

    Invoke-RestMethod -Method Post -Uri "$api/questionnaire-drafts" -Headers $author -ContentType "application/json" -Body $draftBody | Out-Null

    $patchBody = @{
      operations = @(
        @{
          operation = "upsert_question"
          question = @{
            id = "project-name"
            prompt = "What should we call this project?"
            output_need_ids = @("need:project_name")
            answer_schema = @{ type = "string" }
            mapping = @{ mode = "direct"; target = "/project_name" }
            presentation = @{ name = "short_text"; version = 1; props = @{} }
            required = $true
            order = 1
          }
        }
      )
    } | ConvertTo-Json -Depth 12

    Invoke-RestMethod -Method Patch -Uri "$api/questionnaire-drafts/$id" -Headers $author -ContentType "application/json" -Body $patchBody | Out-Null
    Invoke-RestMethod -Method Post -Uri "$api/questionnaire-drafts/$id/publish" -Headers $author | Out-Null

    $session = Invoke-RestMethod -Method Post -Uri "$api/sessions" -Headers $resp -ContentType "application/json" -Body (@{ questionnaire_id = $id; questionnaire_version = 1 } | ConvertTo-Json)

    $sessionId = $session.session.id
    "Session ID: $sessionId"
    "Open: http://127.0.0.1:5173/sessions/$sessionId"

## 4) Manual UI assertions

1. Open the printed session URL.
2. Confirm the question "What should we call this project?" is visible.
3. Confirm revision `r1` is visible.
4. Open the Result panel and confirm canonical result is `{}`.
5. Enter `North Star House` and submit.
6. Confirm revision changes to `r2`.
7. Confirm progress shows `1 / 1`.
8. Open Health panel and confirm readiness is shown as ready.
9. Open Result -> Raw and confirm `North Star House` appears.
10. Reload the page and confirm revision remains `r2` and result still contains `North Star House`.

## Optional: run the automated equivalent

The same journey is covered by:

    cd frontend
    npm run test:e2e -- deterministic-interview.spec.ts
