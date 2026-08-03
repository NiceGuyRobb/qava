<!--
Sync Impact Report
- Version change: template (unratified) -> 1.0.0
- Modified principles: none (initial ratification)
- Added principles:
	- I. Output Contract Is Authoritative
	- II. Keep the Runtime Model Simple
	- III. Typed UI Is Part of the Engine
	- IV. Deterministic Correctness, Bounded AI
	- V. Every Answer Produces Useful Output
	- VI. Health Must Be Explainable
	- VII. Compile Flexibility into Stability
- Added sections:
	- Product and MVP Constraints
	- Delivery and Quality Gates
- Removed sections: none
- Templates requiring updates:
	- ✅ .specify/templates/plan-template.md
	- ✅ .specify/templates/spec-template.md
	- ✅ .specify/templates/tasks-template.md
- Runtime guidance reviewed:
	- ✅ README.md (source of initial principles; no update required)
	- ✅ .github/agents/speckit.tasks.agent.md (boundary-test rule updated)
	- ✅ Other .github/agents/speckit.*.agent.md files (no outdated project-specific references)
- Follow-up TODOs: none
-->
# Qava Constitution

## Core Principles

### I. Output Contract Is Authoritative

Every questionnaire and interview behavior MUST trace to a declared output need. The output
contract MUST govern result shape, accepted values, mappings, validation, readiness, and
publication eligibility. Questions, UI choices, agents, persistence, and navigation MUST support
the path from evidence to usable output and MUST NOT become competing sources of truth.

Rationale: Qava exists to produce a specific usable artifact, not merely to collect answers.

### II. Keep the Runtime Model Simple

The runtime MUST remain explainable as published questionnaire plus accepted session answers
producing the next interaction, canonical result draft, and health assessment. New abstractions
MUST preserve this model and justify why a smaller contract or deterministic rule cannot solve the
same problem. Qava MUST NOT become a general workflow language, graph runtime, autonomous
multi-agent platform, or form-code generator.

Rationale: A small core loop keeps behavior comprehensible, testable, and operable.

### III. Typed UI Is Part of the Engine

Question metadata MUST define enough answer semantics and presentation information for the engine
to select a compatible component. Renderers MUST consume domain-neutral component
specifications, preserve the answer schema's machine values, and contain no
questionnaire-specific business logic. Display labels MUST NOT replace stable stored identifiers.

Rationale: The capture control and the typed value it emits are part of correctness, not cosmetic
client behavior.

### IV. Deterministic Correctness, Bounded AI

Schemas, identifiers, mappings, accepted values, contract satisfaction, readiness, and
publication MUST be deterministic, enforceable, and auditable. AI MAY propose, rank, rephrase,
clarify, or extract only within declared policy and typed contracts. AI MUST NOT fabricate or
silently replace answers, mutate a published contract, bypass validation, create undeclared
destination fields, or cause publication. Every AI-assisted path MUST have a deterministic
fallback sufficient to keep the core interview operable.

Rationale: Judgment can improve the interview, but correctness and side effects require explicit,
reproducible rules.

### V. Every Answer Produces Useful Output

After every accepted answer or answer edit, the system MUST recalculate affected applicability,
mappings, projection, provenance, health, and readiness, then return an inspectable canonical
result draft. Mapping or validation failures MUST surface as attention items and MUST NOT silently
corrupt the result. External publication MUST occur only through an explicit action.

Rationale: Users and downstream systems must be able to inspect trustworthy progress without
waiting for interview completion.

### VI. Health Must Be Explainable

Every health score and readiness state MUST derive from published, inspectable rules and MUST be
accompanied by dimensions, supporting evidence, and concrete attention items. Health MUST measure
fitness of the projected result rather than question count, and an AI opinion MUST NOT be the sole
basis of a score or publication gate.

Rationale: A headline score is useful only when its cause and remediation are visible.

### VII. Compile Flexibility into Stability

Authoring and runtime execution MUST remain separate phases. Authoring MAY use inference and human
confirmation, but publication MUST produce a self-contained, immutable, versioned questionnaire.
Runtime adaptation MUST stay within its published policy, and generated interactions and
publication outcomes MUST be persisted sufficiently for resume, audit, and reproducibility.
Changing machine meaning after publication MUST create a new questionnaire version.

Rationale: Flexible design must become stable execution so sessions remain resumable, testable,
and reproducible.

## Product and MVP Constraints

- The MVP MUST prove the complete contract-to-question-to-answer-to-projection-to-publication loop
	with typed JSON as the canonical result and JSON Schema as the output contract.
- Output destinations MUST translate the canonical result through adapters. Destination concerns
	MUST NOT leak into questionnaire or session semantics.
- Published definitions, interactions, accepted answers, revisions, and publication receipts MUST
	retain stable identities and sufficient provenance for audit and replay of deterministic state.
- Concurrent session mutation MUST detect stale revisions rather than silently overwrite accepted
	work.
- The MVP MUST favor one coherent end-to-end path over breadth. Unrestricted agents, arbitrary
	code execution, runtime contract mutation, continuous external writes, automatic cross-version
	migration, and additional adapters before the JSON path is proven are out of scope.

## Delivery and Quality Gates

- Each specification MUST identify its output-contract impact, typed interaction impact, AI policy
	boundary, projection and health behavior, publication behavior, and relevant audit evidence.
- Each implementation plan MUST pass the seven core-principle checks before research and again
	after design. Any exception MUST be documented in Complexity Tracking with the rejected simpler
	alternative.
- Contract schemas and examples MUST validate before merge. Changes to schemas, mappings,
	component compatibility, projection, readiness, publication, concurrency, or immutable-version
	behavior MUST include automated contract or integration tests at the affected boundary.
- Each user-story slice MUST preserve an end-to-end path from typed answer capture to an
	inspectable result draft. Work MAY be staged, but no stage may replace the canonical result or
	deterministic fallback with a temporary competing model.
- Reviews MUST verify explicit publication, stable identifiers, validation failures, answer-edit
	recalculation, deterministic fallback, provenance, and auditability wherever those concerns are
	touched.

## Governance

This constitution governs all specifications, plans, tasks, implementation, and reviews. The
README supplies product context and feature detail, but conflicts MUST be resolved in favor of
this constitution until an amendment is ratified.

Amendments MUST document the changed principles, rationale, affected templates or artifacts, and
any migration required for active work. Approval requires an explicit review of the Sync Impact
Report. Constitution versions follow semantic versioning: MAJOR for incompatible governance or
principle changes, MINOR for new principles or materially expanded obligations, and PATCH for
non-semantic clarification. The ratification date remains the original adoption date; the last
amended date changes on every approved amendment.

Every feature plan and code review MUST demonstrate compliance with applicable MUST statements.
Violations MUST block progression unless the constitution itself is amended; Complexity Tracking
may justify complexity but cannot waive a principle. Generated specs, plans, and tasks MUST retain
traceability from user value through requirements, tests, and implementation work.

**Version**: 1.0.0 | **Ratified**: 2026-07-25 | **Last Amended**: 2026-07-25
