# Run from the repository root after starting the backend on port 8000.
# The frontend session URL uses the default Vite port 5173.

$ErrorActionPreference = 'Stop'

$api = 'http://127.0.0.1:8000/api/v1'
$frontend = 'http://127.0.0.1:5173'
$questionnaireId = 'high-end-custom-home-buyer-intake'
$definitionPath = 'data/definitions/custom-home-intake/v1/definition.json'
$payloadPath = Join-Path $env:TEMP "$questionnaireId-publish.json"
$compilerPath = Join-Path $env:TEMP 'compile-qava-definition.py'

$authorHeaders = @{
    'X-Qava-Identity' = '{"actor_id":"custom-home-author","roles":["author"]}'
}
$respondentHeaders = @{
    'X-Qava-Identity' = '{"actor_id":"buyer-001","roles":["respondent"]}'
}

@'
import json
import sys
from pathlib import Path

from qava.infrastructure.contracts.definition_pack import load_definition_pack

pack = load_definition_pack(Path(sys.argv[1]))
payload = {
    "title": "High-End Custom Home Buyer Intake",
    "description": (
        "A structured planning brief for high-end custom home buyers. "
        "It gives the builder, architect, designer, and specialty subcontractors "
        "a shared, traceable basis for scope, site, lifestyle, structure, finishes, "
        "outdoor living, budget, delivery priorities, and trade-offs."
    ),
    "output_contract": pack.output_contract,
    "questions": pack.questions,
    "decisions": [],
}
Path(sys.argv[2]).write_text(json.dumps(payload, indent=2), encoding="utf-8")
'@ | Set-Content -Path $compilerPath -Encoding utf8

uv run --project backend python $compilerPath $definitionPath $payloadPath
$payload = Get-Content $payloadPath -Raw | ConvertFrom-Json -AsHashtable

try {
    $draft = Invoke-RestMethod `
        -Method Get `
        -Uri "$api/questionnaire-drafts/$questionnaireId" `
        -Headers $authorHeaders
}
catch {
    $draft = Invoke-RestMethod `
        -Method Post `
        -Uri "$api/questionnaire-drafts" `
        -Headers $authorHeaders `
        -ContentType 'application/json' `
        -Body (@{
            id = $questionnaireId
            title = $payload.title
            description = $payload.description
            output_contract = $payload.output_contract
        } | ConvertTo-Json -Depth 100)
}

$draft = Invoke-RestMethod `
    -Method Put `
    -Uri "$api/questionnaire-drafts/$questionnaireId/raw" `
    -Headers $authorHeaders `
    -ContentType 'application/json' `
    -Body (Get-Content $payloadPath -Raw)

if ($draft.validation_issues.Count -gt 0) {
    $draft.validation_issues | Format-Table code, message, pointer -AutoSize
    throw 'The draft has validation issues and was not published.'
}

$published = Invoke-RestMethod `
    -Method Post `
    -Uri "$api/questionnaire-drafts/$questionnaireId/publish" `
    -Headers $authorHeaders

$version = $published.version
$questionnaire = Invoke-RestMethod `
    -Method Get `
    -Uri "$api/questionnaires/$questionnaireId/versions/$version" `
    -Headers $authorHeaders

$session = Invoke-RestMethod `
    -Method Post `
    -Uri "$api/sessions" `
    -Headers $respondentHeaders `
    -ContentType 'application/json' `
    -Body (@{
        questionnaire_id = $questionnaire.questionnaire_id
        questionnaire_version = $questionnaire.version
    } | ConvertTo-Json)

$sessionId = $session.session.id

Write-Host "Published questionnaire version: $($questionnaire.version)"
Write-Host "New session ID: $sessionId"
Write-Host "Open: $frontend/sessions/$sessionId"

# Existing sessions remain pinned to their original questionnaire version.