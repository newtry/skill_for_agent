# Test Coverage Checklist

Use this checklist selectively. Start with business risk and document why a relevant high-risk area is excluded.

## Business Behavior

- Primary journey and each acceptance criterion
- Alternate, cancellation, rejection, and recovery journeys
- Business calculations, rounding, currency, discounts, taxes, totals, and reconciliation
- Lifecycle states, legal transitions, repeated transitions, terminal states, and compensation
- Cross-feature and downstream effects
- Notifications, documents, exports, and operator follow-up actions

## Inputs And Data

- Required, optional, empty, null, malformed, duplicate, and unsupported values
- Minimum, maximum, just-inside, just-outside, zero, negative, and precision boundaries
- Unicode, long text, whitespace, case, locale, timezone, and daylight-saving behavior
- Referential integrity, uniqueness, ordering, pagination, filtering, and aggregation
- Seed data, tenant isolation, data ownership, retention, deletion, and anonymization
- Historical, migrated, stale, partially populated, and backward-compatible records

## Interfaces And Integrations

- Request and response schema, status or error contract, and version compatibility
- Authentication, authorization, signing, validation, and rate limiting
- Timeout, connection loss, retry, backoff, circuit breaking, and fallback
- Duplicate delivery, idempotency, out-of-order events, replay, and eventual consistency
- Partial success, atomicity, rollback, compensation, and reconciliation
- Dependency degradation, malformed dependency response, and sandbox versus production differences

## Concurrency And Time

- Simultaneous creates, updates, reservations, approvals, and cancellations
- Lost update, double submission, locking, optimistic concurrency, and deduplication
- Clock boundaries, cutoff times, date ranges, expiry, scheduled jobs, and delayed events
- Retry after timeout when the first request may already have committed

## Security And Safety

- Role, tenant, ownership, field-level, and action-level permission boundaries
- Direct-object access, injection, unsafe file handling, secret leakage, and sensitive logs
- Destructive or high-impact action confirmation, auditability, and reversibility
- Abuse limits, unsafe content, prompt injection, and tool escalation for AI systems

## Quality Attributes

- Expected load, peak load, latency percentile, throughput, resource limits, and graceful degradation
- Availability, restart, failover, recovery point, recovery time, and backup restoration
- Browser, device, operating system, API, database, and deployment compatibility
- Accessibility, localization, usability of failures, and operator diagnostics
- Logs, metrics, traces, audit events, correlation or run IDs, and actionable alerts

## Deployment And Change Risk

- Feature flag off, on, rollout percentage, rollback, and mixed-version operation
- Schema expansion, backfill, migration, rollback, and old-client compatibility
- Cache invalidation, configuration defaults, environment differences, and secret rotation
- Directly changed behavior plus callers, consumers, reports, jobs, and stored data affected by it

## AI And Agent Behavior

- Deterministic routing, parsing, validation, policy, formatting, and fallback tests
- Evaluation dataset representativeness, expected labels, scoring metric, and pass threshold
- Ambiguous, incomplete, contradictory, adversarial, and out-of-domain inputs
- Hallucination controls, evidence grounding, uncertainty, and abstention
- Tool choice, argument validation, permission, confirmation, idempotency, and side effects
- Run trace, replay fixture, model and prompt version, feedback capture, and audit trail
- Repeatability policy and separation of offline CI from live-model evaluation

## Test Suite Quality

- One clear purpose and pass/fail decision per case
- Stable requirement and case IDs
- Explicit preconditions, data, steps, expected results, and cleanup
- No dependence on execution order unless declared
- No vague assertions or undocumented assumptions
- Clear ownership, automation suitability, environment, and labels
- Traceability for covered, partially covered, blocked, and intentionally excluded requirements
