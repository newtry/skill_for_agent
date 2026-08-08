---
name: derive-test-cases
description: Derive reviewable, traceable, and executable test cases from product requirements, PRDs, user stories, acceptance criteria, technical designs, API contracts, data models, workflow diagrams, or change proposals. Use when Codex needs to plan functional, integration, end-to-end, regression, migration, security, performance, or AI-agent tests; build a requirements-to-tests traceability matrix; review test coverage; identify ambiguous or conflicting requirements; or turn a product and engineering design into a test case specification or automation plan.
---

# Derive Test Cases

Turn requirements and designs into evidence-based test coverage. Preserve traceability from every case to its source, surface gaps instead of inventing business rules, and make expected results precise enough to decide pass or fail.

## Choose The Mode

Select the smallest mode that satisfies the request:

- **Generate**: create a complete test specification from source documents.
- **Review**: inspect existing cases against requirements and report missing, duplicate, stale, or unverifiable coverage.
- **Delta**: focus on changed requirements or designs, then identify direct tests and regression impact.
- **Automate**: convert approved cases into an automation plan or test code only when requested.

Default to Generate when the user asks to “梳理测试用例” without another mode.

## Gather Evidence

1. Read all user-provided requirement and design sources before drafting cases.
2. Read repository instructions such as `AGENTS.md`, testing documentation, existing nearby tests, schemas, API contracts, domain glossaries, and architecture decisions when available.
3. Search before reading large repositories. Locate feature terms, involved modules, current tests, data models, events, permissions, and error codes.
4. Record every source by path, section, requirement ID, issue ID, or URL. Use stable source references where possible.
5. Apply this precedence unless project rules say otherwise:
   - explicitly approved acceptance criteria and recorded product decisions;
   - current requirement specification;
   - current technical design and contracts;
   - current implementation and tests as evidence of existing behavior.
6. Do not silently resolve conflicts between sources. List the conflict and its effect on testability.

If a required source is missing, proceed with the available evidence when useful, clearly label the result as a draft, and list the missing inputs.

## Build A Requirement Inventory

Normalize the source material into atomic requirement units. Assign temporary IDs such as `REQ-001` only when stable IDs do not exist.

For each unit, capture:

- actor or caller;
- trigger and preconditions;
- business rule or decision;
- successful outcome and externally visible side effects;
- failure, rejection, cancellation, or compensation behavior;
- state transition and persisted data;
- permissions and tenant or ownership scope;
- timing, volume, compatibility, security, audit, and observability constraints;
- unresolved assumptions or ambiguities.

Split compound statements when each clause can pass or fail independently. Preserve the original source reference on every unit.

## Model Test Conditions

Derive test conditions before writing detailed cases:

1. Cover the primary business journey first.
2. Apply equivalence classes and boundary values to inputs, amounts, counts, dates, sizes, limits, and pagination.
3. Use decision tables for interacting rules and state-transition coverage for lifecycle workflows.
4. Cover invalid inputs, unavailable dependencies, timeout and retry behavior, duplicate requests, partial success, rollback or compensation, and recovery.
5. Cover role, tenant, ownership, and data-scope boundaries.
6. Trace technical design components to contract, persistence, integration, compatibility, deployment, and observability tests.
7. Read [coverage-checklist.md](references/coverage-checklist.md) and apply only relevant dimensions. State why a high-risk dimension is not applicable.

Do not inflate case counts by mechanically combining every dimension. Use pairwise or risk-based combinations unless a rule interaction, financial impact, inventory impact, security boundary, or destructive action requires exhaustive coverage.

## Write Executable Cases

Give every case a stable ID such as `TC-<FEATURE>-001`. Write one independently decidable behavior per case.

Each detailed case must include:

- priority and test level;
- linked requirement IDs and source references;
- objective;
- preconditions;
- explicit test data;
- numbered actions;
- observable expected results for each meaningful action or checkpoint;
- cleanup or data restoration when needed;
- automation recommendation and rationale;
- labels such as smoke, regression, security, migration, or manual.

Expected results must specify what can be observed through UI, API response, events, database state, external calls, audit records, logs, metrics, or user-visible status. Avoid vague outcomes such as “works normally”, “returns correctly”, or “data is accurate”.

Never invent unavailable field names, status codes, thresholds, or business calculations. Mark them `TBD` and link them to an open question. Use example values only when clearly labeled as examples.

## Prioritize By Business Risk

Use the project’s priority rules when defined. Otherwise assign:

- **P0**: money, inventory, order correctness, authorization, tenant isolation, irreversible writes, data loss, regulatory or privacy exposure, or a primary workflow that blocks business.
- **P1**: important alternate paths, recoverable integration failures, operational efficiency, compatibility, and high-frequency edge cases.
- **P2**: low-frequency, low-impact presentation, convenience, and minor compatibility cases.

Prioritize user outcomes over implementation details. A unit test can be P0 if it protects a critical calculation; an end-to-end test is not automatically P0.

## Handle AI And Agent Workflows

When the design includes an LLM, classifier, recommendation, tool call, or autonomous action:

- separate deterministic business rules from probabilistic model quality;
- test tool permissions, confirmation boundaries, idempotency, side effects, and safe failure deterministically;
- verify evidence, citations, run IDs, replay inputs, decision traces, and feedback persistence when the product exposes them;
- define fixture-based offline tests for parsing, routing, policy, formatting, and fallback behavior;
- define evaluation datasets, quality metrics, thresholds, and repeat-run policy for model behavior;
- keep live-model or external-service evaluations outside ordinary deterministic CI unless the project explicitly requires them;
- test misleading, ambiguous, incomplete, unsafe, and cross-tenant prompts relevant to the business.

Do not use subjective expected results such as “the answer is good”. Specify measurable or reviewable criteria.

## Produce The Deliverable

Follow the user’s requested format. Otherwise produce a concise Markdown specification in this order:

1. scope and source baseline;
2. assumptions, conflicts, and open questions;
3. requirement-to-test traceability matrix;
4. detailed test cases grouped by business flow or component;
5. automation and test-data plan;
6. coverage summary and residual risks.

Write in the user's language. Prefer established domain terms and action-oriented wording over internal field names or testing jargon in business-facing summaries.

Use [test-case-spec-template.md](assets/test-case-spec-template.md) as the base when creating a standalone file. Adapt sections rather than leaving empty boilerplate.

For large suites, show the matrix and high-risk cases first, then write the complete suite to a file. Keep business-facing summaries short and action-oriented.

## Validate Before Delivery

Check all of the following:

- every in-scope requirement maps to at least one test or an explicit reason for no test;
- every P0 rule has positive, negative, boundary, authorization, failure, and recovery coverage where applicable;
- every case maps back to a real requirement, risk, contract, or regression concern;
- expected results are observable and unambiguous;
- cases specify sufficient data and preconditions to reproduce them;
- duplicate cases are merged without losing distinct risk coverage;
- automated, manual, live-service, and non-CI tests are clearly separated;
- open questions name the affected requirements and blocked cases;
- out-of-scope behavior and residual risk are explicit;
- repository test commands and placement conventions are included when automation is requested.

Do not claim full coverage merely because all document headings have a test. Report semantic coverage, known gaps, and confidence based on source quality.
