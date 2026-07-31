"""Shared pytest fixtures for all backend tests."""

from __future__ import annotations

from typing import Any

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture
def multi_shape_questionnaire() -> dict[str, Any]:
    """A questionnaire exercising the full typed-capture surface.

    Covers a runtime option source (component catalog), a nested collection
    (repeatable group of objects), and money + date/time controls. Questions are
    in the draft ``upsert_question`` shape so integration tests can publish it via
    the API, while unit tests can pick individual questions apart.
    """
    output_contract: dict[str, Any] = {
        "type": "object",
        "properties": {
            "component": {"type": "string"},
            "rooms": {"type": "array"},
            "budget": {"type": "number"},
            "start_date": {"type": "string"},
            "appointment": {"type": "string"},
        },
        "required": ["component"],
    }
    questions: list[dict[str, Any]] = [
        {
            "id": "q-component",
            "prompt": "Which component fits best?",
            "output_need_ids": ["need:component"],
            "answer_schema": {"type": "string"},
            "option_source": {"provider": "component_catalog", "select": "components"},
            "mapping": {"mode": "direct", "target": "/component"},
            "component": "single_select",
            "required": True,
            "order": 1,
        },
        {
            "id": "q-rooms",
            "prompt": "List the rooms.",
            "output_need_ids": ["need:rooms"],
            "answer_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "area": {"type": "number"},
                    },
                    "required": ["name"],
                },
            },
            "mapping": {"mode": "direct", "target": "/rooms"},
            "component": "repeatable_group",
            "required": False,
            "order": 2,
        },
        {
            "id": "q-budget",
            "prompt": "What is the budget?",
            "output_need_ids": ["need:budget"],
            "answer_schema": {"type": "number", "minimum": 0},
            "props": {"currency": "USD"},
            "mapping": {"mode": "direct", "target": "/budget"},
            "component": "money_input",
            "required": False,
            "order": 3,
        },
        {
            "id": "q-start",
            "prompt": "When does it start?",
            "output_need_ids": ["need:start_date"],
            "answer_schema": {"type": "string", "format": "date"},
            "mapping": {"mode": "direct", "target": "/start_date"},
            "component": "date_picker",
            "required": False,
            "order": 4,
        },
        {
            "id": "q-appointment",
            "prompt": "Pick an appointment time.",
            "output_need_ids": ["need:appointment"],
            "answer_schema": {"type": "string", "format": "date-time"},
            "mapping": {"mode": "direct", "target": "/appointment"},
            "component": "datetime_picker",
            "required": False,
            "order": 5,
        },
    ]
    return {"output_contract": output_contract, "questions": questions}
