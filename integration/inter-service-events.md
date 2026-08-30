# CodeGuru Inter-Service Events — Contract v1

> **What this is:** the async half of the integration (the sync half is
> [README.md](README.md)). When Code Coach
> *detects* something, it publishes an event; interested services react
> without Code Coach knowing or caring who they are. Transport is **Google
> Pub/Sub** in production; the JSON contract below is transport-agnostic, so
> local testing can POST the same bodies directly to your endpoint.

## Why events and not REST calls

If Code Coach called Study Guider's REST API directly on every struggle:
Code Coach must know Study Guider's URL, be deployed after it, handle its
downtime, and add a call per new consumer. With publish/subscribe, Code Coach
emits a fact — *"this student is struggling with loops"* — and any number of
services subscribe independently. Loose coupling is the whole point of the
microservice split.

## Topics

| Topic | Published when | Expected consumers |
|---|---|---|
| `codeguru.remediation.triggered` | struggle/hint-dependency analysis creates or escalates a remediation trigger | Study Guider |
| `codeguru.learning-event.created` | any learning event is stored (hint shown, issue resolved, quiz completed, ...) | Gamification Engine |

## Envelope (every message)

```json
{
  "event_id": "evt_1f2a...",           // unique — deduplicate on this
  "event_version": 1,                  // bump on breaking change
  "occurred_at": "2026-07-12T10:22:41Z",
  "source": "code-coach",
  "type": "remediation.triggered",
  "data": { ... }                      // type-specific payload below
}
```

## Payloads

### `remediation.triggered` → Study Guider

```json
{
  "trigger_id": "trig_8c1d...",
  "user_id": "user_c94da...",
  "concept_tag": "array_indexing",
  "error_type": "OFF_BY_ONE_LOOP_BOUNDARY",
  "struggle_level": "high",            // low | medium | high
  "struggle_score": 0.82,
  "hint_dependency_level": "medium",   // low | medium | high
  "recommended_action": "micro_lesson",
  "repeat_count": 4
}
```

Consumer contract: fetch full details / act via
`GET /api/v1/remediation/me/recommendations` (with the student's token), then
report back with the `lesson-opened` / `quiz-completed` endpoints.

### `learning-event.created` → Gamification

```json
{
  "learning_event_id": "evt_9a3b...",
  "user_id": "user_c94da...",
  "learning_session_id": "ls_e205...",
  "event_type": "diagnostic_resolved",  // or hint_level_requested, quiz_completed, ...
  "concept_tag": "array_indexing",
  "payload": { "error_type": "OFF_BY_ONE_LOOP_BOUNDARY" }
}
```

## Transport: Google Pub/Sub on Cloud Run

- **Publish** (Code Coach): `google-cloud-pubsub` client →
  `topics/codeguru.remediation.triggered`.
- **Subscribe** (your service): create a **push subscription** pointing at an
  HTTPS endpoint you expose, e.g. `POST /internal/events`. Pub/Sub wraps the
  message as `{"message": {"data": "<base64 of the JSON above>", ...}}` —
  base64-decode `message.data`, then parse.
- **Acknowledge** by returning 2xx. Non-2xx → Pub/Sub retries with backoff, so
  make handlers **idempotent** (deduplicate on `event_id`).
- Ordering is not guaranteed; use `occurred_at` if sequence matters.

### Local testing without Pub/Sub

POST the raw envelope JSON straight to your handler — the body inside
`message.data` is exactly the envelope above. A curl fixture per topic lives
in this contract; no emulator needed for basic testing.

## Status & rollout

- **Contract:** stable as of 2026-07-12 — build consumers against it now.
- **Publisher:** Code Coach currently persists triggers/events and exposes
  them over REST; the Pub/Sub publish call is added when the team enables
  Pub/Sub on the shared project (one `publisher.publish()` in
  remediation_service / events route — small, isolated change).
- Until then, consumers can poll the equivalent REST endpoints; the payload
  shapes are identical, so switching to push later costs nothing.
