"""Interviewing application service: session create, answer, skip, navigate."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from qava.application.assistance import AssistanceService
from qava.application.options import OptionResolutionService
from qava.domain.answers import validate_answer
from qava.domain.evaluation import SessionEvaluation, evaluate_session
from qava.domain.models import (
    InteractionId,
    NavigationFocus,
    PublishedQuestionnaireRecord,
    QuestionnaireId,
    RuntimeInteractionRecord,
    SessionId,
    SessionRecord,
    SkipDisposition,
)
from qava.infrastructure.database.repositories import (
    SQLiteInteractionRepository,
    SQLitePublishedQuestionnaireRepository,
    SQLiteSessionRepository,
)


class StaleRevisionError(Exception):
    pass


class InterviewingService:
    def __init__(
        self,
        questionnaire_repo: SQLitePublishedQuestionnaireRepository,
        session_repo: SQLiteSessionRepository,
        interaction_repo: SQLiteInteractionRepository,
        option_service: OptionResolutionService | None = None,
        assistance_service: AssistanceService | None = None,
    ) -> None:
        self._questionnaires = questionnaire_repo
        self._sessions = session_repo
        self._interactions = interaction_repo
        self._options = option_service or OptionResolutionService()
        self._assistance = assistance_service

    async def create_session(
        self,
        *,
        questionnaire_id: str,
        questionnaire_version: int,
        created_by: str,
    ) -> dict[str, Any] | None:
        questionnaire = await self._questionnaires.get(
            QuestionnaireId(questionnaire_id), questionnaire_version
        )
        if questionnaire is None:
            return None

        now = datetime.now(UTC)
        session = SessionRecord(
            session_id=SessionId(str(uuid.uuid4())),
            questionnaire_id=QuestionnaireId(questionnaire_id),
            questionnaire_version=questionnaire_version,
            revision=1,
            status="active",
            active_topic_id=None,
            answers={},
            generated_interactions=[],
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        await self._sessions.create(session)
        if self._assistance is not None:
            await self._assistance.propose(
                session_id=str(session.session_id),
                operation="ranking",
                policy=questionnaire.assistance_policy,
                context={
                    "eligible_interaction_ids": [
                        question["id"]
                        for question in questionnaire.questions
                        if isinstance(question.get("id"), str)
                    ]
                },
            )
        return _session_view(session, questionnaire, self._options)

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            return None
        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            return None
        return _session_view(session, questionnaire, self._options)

    async def submit_answer(
        self,
        session_id: str,
        *,
        question_id: str,
        value: Any,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )
        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        question = next((q for q in questionnaire.questions if q.get("id") == question_id), None)
        if question is None:
            raise ValueError(f"Question {question_id!r} not found in questionnaire.")
        issues = validate_answer(self._options.question_for_validation(question), value)
        if issues:
            raise ValueError(f"Answer validation failed: {issues[0]}")

        new_answers = {**session.answers, question_id: value}
        # Clear skip disposition for the answered question
        new_skips = {k: v for k, v in session.skip_dispositions.items() if k != question_id}
        # Clear navigation focus if it targeted this question
        new_focus = session.navigation_focus
        if new_focus is not None and new_focus.question_id == question_id:
            new_focus = None

        now = datetime.now(UTC)
        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=new_answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=session.active_topic_id,
            skip_dispositions=_skip_dispositions_to_raw(new_skips),
            navigation_focus=_navigation_focus_to_raw(new_focus),
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        await self._interactions.append(RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="answer_accepted",
            interaction_snapshot=question,
            submitted_value=value,
            actor_id=actor_id,
            metadata={},
            created_at=now,
        ))
        return _session_view(updated, questionnaire, self._options)

    async def skip_interaction(
        self,
        session_id: str,
        *,
        question_id: str,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )
        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        evaluation = evaluate_session(questionnaire, session)
        if "skip" not in evaluation.permitted_actions:
            raise ValueError("Skip not permitted for the current interaction.")

        now = datetime.now(UTC)
        new_skips = {
            **_skip_dispositions_to_raw(session.skip_dispositions),
            question_id: {
                "question_id": question_id,
                "accepted_revision": session.revision,
                "actor_id": actor_id,
                "skipped_at": now.isoformat(),
            },
        }
        # Clear navigation focus if it targeted this question
        new_focus = session.navigation_focus
        if new_focus is not None and new_focus.question_id == question_id:
            new_focus = None

        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=session.answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=session.active_topic_id,
            skip_dispositions=new_skips,
            navigation_focus=_navigation_focus_to_raw(new_focus),
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        await self._interactions.append(RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="skip",
            interaction_snapshot=None,
            submitted_value=None,
            actor_id=actor_id,
            metadata={"question_id": question_id},
            created_at=now,
        ))
        return _session_view(updated, questionnaire, self._options)

    async def navigate(
        self,
        session_id: str,
        *,
        section_id: str | None = None,
        output_need_id: str | None = None,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )
        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        evaluation = evaluate_session(questionnaire, session)

        # Resolve target question
        target_question_id: str | None = None
        if output_need_id is not None:
            # Must be in unresolved needs
            unresolved_ids = {n["id"] for n in evaluation.unresolved_needs}
            if output_need_id not in unresolved_ids:
                raise ValueError(
                    f"Output need {output_need_id!r} is not unresolved or does not exist."
                )
            target_question_id = next(
                (
                    q.get("id")
                    for q in questionnaire.questions
                    if output_need_id in q.get("output_need_ids", [])
                    and q.get("id") in evaluation.applicable_question_ids
                ),
                None,
            )
            if target_question_id is None:
                raise ValueError(
                    f"No applicable question found for output need {output_need_id!r}."
                )
        elif section_id is not None:
            # Find first eligible question in that topic
            target_question_id = next(
                (
                    q.get("id")
                    for q in questionnaire.questions
                    if q.get("topic_id") == section_id
                    and q.get("id") in evaluation.applicable_question_ids
                    and q.get("id") not in evaluation.active_answer_ids
                    and q.get("id") not in evaluation.active_skip_ids
                ),
                None,
            )
            if target_question_id is None:
                raise ValueError(
                    f"No eligible question found in section {section_id!r}."
                )

        now = datetime.now(UTC)
        new_focus = (
            None
            if target_question_id is None
            else {
                "question_id": target_question_id,
                "output_need_id": output_need_id,
                "topic_id": section_id,
                "accepted_revision": session.revision,
                "actor_id": actor_id,
            }
        )
        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=session.answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=section_id or session.active_topic_id,
            skip_dispositions=_skip_dispositions_to_raw(session.skip_dispositions),
            navigation_focus=new_focus,
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        await self._interactions.append(RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="navigation",
            interaction_snapshot=None,
            submitted_value=None,
            actor_id=actor_id,
            metadata={
                "target_question_id": target_question_id,
                "target_topic_id": section_id,
                "output_need_id": output_need_id,
            },
            created_at=now,
        ))
        return _session_view(updated, questionnaire, self._options)

    async def delete_session(self, session_id: str) -> bool:
        return await self._sessions.delete(SessionId(session_id))


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


def _session_view(
    session: SessionRecord,
    questionnaire: PublishedQuestionnaireRecord,
    options: OptionResolutionService,
) -> dict[str, Any]:
    ev = evaluate_session(questionnaire, session)
    result_status = "ready" if ev.health.readiness == "ready" else "in_progress"
    current_interaction = options.augment_interaction(ev.current_interaction)
    return {
        "session": {
            "id": str(session.session_id),
            "questionnaire_id": str(session.questionnaire_id),
            "questionnaire_version": session.questionnaire_version,
            "revision": session.revision,
            "status": "completed" if ev.current_interaction is None else "active",
        },
        "progress": {
            "satisfied_required": ev.progress.satisfied_required,
            "total_required": ev.progress.total_required,
        },
        "current_interaction": current_interaction,
        "result": {
            "session_id": str(session.session_id),
            "revision": session.revision,
            "status": result_status,
            "data": ev.projection.data,
            "provenance": {
                path: evidence.get("question_ids", [])
                for path, evidence in ev.projection.provenance.items()
            },
            "unresolved_output_needs": ev.unresolved_needs,
            "issues": [],
        },
        "health": {
            "revision": session.revision,
            "score": ev.health.score,
            "readiness": ev.health.readiness,
            "dimensions": ev.health.dimensions,
            "attention": [a.model_dump() for a in ev.health.attention],
            "calculation_version": ev.health.calculation_version,
        },
        "actions": ev.permitted_actions,
        "changed_paths": ev.projection.changed_paths,
    }


# ---------------------------------------------------------------------------
# Serialisation helpers for disposition / focus
# ---------------------------------------------------------------------------


def _skip_dispositions_to_raw(
    dispositions: dict[str, SkipDisposition],
) -> dict[str, Any]:
    return {
        qid: {
            "question_id": d.question_id,
            "accepted_revision": d.accepted_revision,
            "actor_id": d.actor_id,
            "skipped_at": d.skipped_at.isoformat(),
        }
        for qid, d in dispositions.items()
    }


def _navigation_focus_to_raw(focus: NavigationFocus | None) -> dict[str, Any] | None:
    if focus is None:
        return None
    return {
        "question_id": focus.question_id,
        "output_need_id": focus.output_need_id,
        "topic_id": focus.topic_id,
        "accepted_revision": focus.accepted_revision,
        "actor_id": focus.actor_id,
    }


    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            return None
        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            return None
        return _build_session_view(session, questionnaire)

    async def submit_answer(
        self,
        session_id: str,
        *,
        question_id: str,
        value: Any,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)

        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )

        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        question = next((q for q in questionnaire.questions if q.get("id") == question_id), None)
        if question is None:
            raise ValueError(f"Question {question_id!r} not found in questionnaire.")

        issues = validate_answer(question, value)
        if issues:
            raise ValueError(f"Answer validation failed: {issues[0]}")

        new_answers = dict(session.answers)
        new_answers[question_id] = value

        now = datetime.now(UTC)
        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=new_answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=session.active_topic_id,
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        interaction = RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="answer_accepted",
            interaction_snapshot=question,
            submitted_value=value,
            actor_id=actor_id,
            metadata={},
            created_at=now,
        )
        await self._interactions.append(interaction)

        return _build_session_view(updated, questionnaire)

    async def skip_interaction(
        self,
        session_id: str,
        *,
        question_id: str,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )

        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        now = datetime.now(UTC)
        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=session.answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=session.active_topic_id,
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        skip_record = RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="skip",
            interaction_snapshot=None,
            submitted_value=None,
            actor_id=actor_id,
            metadata={"question_id": question_id},
            created_at=now,
        )
        await self._interactions.append(skip_record)

        return _build_session_view(updated, questionnaire)

    async def navigate(
        self,
        session_id: str,
        *,
        section_id: str | None = None,
        output_need_id: str | None = None,
        expected_revision: int,
        actor_id: str,
    ) -> dict[str, Any]:
        session = await self._sessions.get(SessionId(session_id))
        if session is None:
            raise KeyError(session_id)
        if session.revision != expected_revision:
            raise StaleRevisionError(
                f"Expected revision {expected_revision}, current is {session.revision}."
            )

        questionnaire = await self._questionnaires.get(
            session.questionnaire_id, session.questionnaire_version
        )
        if questionnaire is None:
            raise KeyError(session.questionnaire_id)

        target_question_id = None
        if output_need_id is not None:
            target_question_id = next(
                (
                    question.get("id")
                    for question in questionnaire.questions
                    if output_need_id in question.get("output_need_ids", [])
                ),
                None,
            )
            if not isinstance(target_question_id, str):
                raise KeyError(output_need_id)

        now = datetime.now(UTC)
        updated = await self._sessions.update_with_revision(
            SessionId(session_id),
            expected_revision=expected_revision,
            answers=session.answers,
            generated_interactions=session.generated_interactions,
            status=session.status,
            active_topic_id=section_id or session.active_topic_id,
            updated_at=now,
        )
        if updated is None:
            raise StaleRevisionError("Session was updated concurrently.")

        nav_record = RuntimeInteractionRecord(
            interaction_id=InteractionId(str(uuid.uuid4())),
            session_id=SessionId(session_id),
            session_revision=updated.revision,
            kind="navigation",
            interaction_snapshot=None,
            submitted_value=None,
            actor_id=actor_id,
            metadata={
                "target_question_id": target_question_id,
                "target_topic_id": section_id,
                "output_need_id": output_need_id,
            },
            created_at=now,
        )
        await self._interactions.append(nav_record)

        return _build_session_view(updated, questionnaire)

    async def delete_session(self, session_id: str) -> bool:
        return await self._sessions.delete(SessionId(session_id))


def _build_session_view(
    session: SessionRecord,
    questionnaire: PublishedQuestionnaireRecord,
) -> dict[str, Any]:
    questions = questionnaire.questions
    answers = dict(session.answers)

    projection = project_result(questions=questions, answers=answers)

    next_candidate = select_next_interaction(questions=questions, answers=answers)
    current_interaction = _runtime_interaction(questions, next_candidate)

    health = assess_health(
        output_needs=questionnaire.output_needs,
        questions=questions,
        answers=answers,
        policy=questionnaire.health_policy,
        revision=session.revision,
    )

    unresolved = _unresolved_needs(questionnaire.output_needs, questions, answers)
    required_needs = [need for need in questionnaire.output_needs if need.get("required")]
    unresolved_required = sum(1 for need in unresolved if need["required"])
    result_status = "ready" if health.readiness == "ready" else "in_progress"
    actions = ["save_and_exit", "delete"]
    if current_interaction is not None:
        actions.extend(["answer", "skip", "navigate"])
    if health.readiness == "ready":
        actions.extend(["preview_publication", "publish"])

    return {
        "session": {
            "id": str(session.session_id),
            "questionnaire_id": str(session.questionnaire_id),
            "questionnaire_version": session.questionnaire_version,
            "revision": session.revision,
            "status": "completed" if current_interaction is None else "active",
        },
        "progress": {
            "satisfied_required": len(required_needs) - unresolved_required,
            "total_required": len(required_needs),
        },
        "current_interaction": current_interaction,
        "result": {
            "session_id": str(session.session_id),
            "revision": session.revision,
            "status": result_status,
            "data": projection.data,
            "provenance": {
                path: evidence.get("question_ids", [])
                for path, evidence in projection.provenance.items()
            },
            "unresolved_output_needs": unresolved,
            "issues": [],
        },
        "health": {
            "revision": session.revision,
            "score": health.score,
            "readiness": health.readiness,
            "dimensions": health.dimensions,
            "attention": [a.model_dump() for a in health.attention],
            "calculation_version": health.calculation_version,
        },
        "actions": actions,
        "changed_paths": projection.changed_paths,
    }


def _runtime_interaction(
    questions: list[dict[str, Any]],
    candidate: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if candidate is None:
        return None

    question_id = candidate.get("question_id")
    question = next((item for item in questions if item.get("id") == question_id), None)
    if question is None:
        return None

    return {
        "id": question["id"],
        "kind": "question",
        "output_need_ids": question.get("output_need_ids", []),
        "prompt": question.get("prompt", ""),
        "reason": question.get("reason", "Collect evidence for the output contract."),
        "required": bool(question.get("required", False)),
        "answer_schema": question.get("answer_schema", {}),
        "component": question.get("presentation", {}),
        "policy_limit": None,
    }


def _unresolved_needs(
    output_needs: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
) -> list[dict[str, Any]]:
    served: set[str] = set()
    for question in questions:
        qid = question.get("id")
        if isinstance(qid, str) and qid in answers:
            for need_id in question.get("output_need_ids", []):
                if isinstance(need_id, str):
                    served.add(need_id)

    unresolved = []
    for need in output_needs:
        need_id = need.get("id")
        if isinstance(need_id, str) and need_id not in served:
            question = next(
                (
                    q
                    for q in questions
                    if need_id in q.get("output_need_ids", [])
                ),
                None,
            )
            if question is None:
                continue
            question_id = question.get("id")
            if not isinstance(question_id, str):
                continue
            topic_id = question.get("topic_id")
            unresolved.append(
                {
                    "id": need_id,
                    "target": need.get("target"),
                    "label": need.get("label"),
                    "required": need.get("required", False),
                    "criticality": need.get("criticality", "normal"),
                    "question_id": question_id,
                    "topic_id": topic_id if isinstance(topic_id, str) else None,
                }
            )
    return unresolved
