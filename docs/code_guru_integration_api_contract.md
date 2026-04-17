# Code Guru Integration API Contract

This document defines the proposed integration contract between Code Coach and the other Code Guru components.

The aim is to standardize:

- authentication conventions
- shared request metadata
- event payloads
- read APIs
- write APIs
- ownership boundaries

This is a planning document only. It does not imply that the endpoints already exist.

## Persistence Assumption

The current planning assumption is:

- shared backend state is stored in **MongoDB Atlas**
- the database name is `code-guru`
- the application reads the connection string from an environment variable named `MONGODB_URI`

The connection string itself must not be hardcoded into source files, docs, commits, or screenshots.

## Secret Handling

Use this rule from the beginning:

- store the MongoDB Atlas connection string only in environment configuration
- use `MONGODB_URI` locally and in deployment environments
- never commit the full URI into the repository
- avoid pasting the credential into shared documentation

Recommended local configuration pattern:

```text
MONGODB_URI=<mongodb atlas connection string>
MONGODB_DB_NAME=code-guru
```

## Related Docs

- [Shared Data Model](C:/Hello/Tutorials/code-coach/docs/code_guru_shared_data_model.md)
- [Phase 1 Implementation Plan](C:/Hello/Tutorials/code-coach/docs/code_guru_phase1_implementation_plan.md)
- [Code Coach Proposal Traceability](C:/Hello/Tutorials/code-coach/docs/proposal_traceability.md)

## API Design Principles

1. Every request must resolve to an authenticated user.
2. Components should communicate through stable APIs and event contracts, not direct collection access.
3. Payloads should be explicit enough for logging, analytics, and later microservice separation.
4. Code Coach should publish diagnostics as structured signals, not just UI messages.
5. Component-specific payload details should live inside controlled JSON shapes, not ad hoc fields.

## Recommended Base Structure

Recommended REST base paths:

- `/api/v1/auth`
- `/api/v1/sessions`
- `/api/v1/diagnostics`
- `/api/v1/events`
- `/api/v1/mastery`
- `/api/v1/remediation`

If services are later separated:

- `auth-service`
- `code-coach-service`
- `progress-tracker-service`
- `gamification-service`
- `collab-service`

For now, one shared backend or API gateway is enough.

## Authentication Contract

### Login Flow

```text
Student logs in
-> receives JWT access token
-> receives refresh token or equivalent re-auth session marker
-> frontend/extension includes token on every request
-> backend resolves user identity from token
-> stored records use backend-trusted user id
```

### Chosen Auth Mode

The current agreed plan is:

- full login UI + JWT from the start

For Phase 1 this implies:

- no manual token paste as the primary user flow
- the VS Code extension must support real authentication UI
- API protection is enforced from the beginning for session creation and analysis routes

### Required Headers

```http
Authorization: Bearer <jwt>
Content-Type: application/json
X-Client-Type: vscode | web | game_ui
X-Request-Id: <uuid>
```

### Auth Response Example

```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
    "student_number": "IT22253958",
    "role": "student"
  }
}
```

### Recommended Auth Endpoints For Phase 1

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

The minimum implementation can simplify refresh behavior, but the extension should not be designed around one-time tokens only.

## Shared Request Context

Every component request should be able to carry this context:

```json
{
  "learning_session_id": "8c7f04cb-2b7a-41e0-8d44-222222222222",
  "task_id": "arrays_lab_01",
  "course_id": "SE4010",
  "language": "java",
  "source_component": "code_coach"
}
```

This context should not replace backend authentication. It only adds session and educational context.

## Core Event Contract

All components should be able to publish events to a shared ingestion endpoint.

### Endpoint

`POST /api/v1/events`

### Generic Event Schema

```json
{
  "learning_session_id": "8c7f04cb-2b7a-41e0-8d44-222222222222",
  "component": "code_coach",
  "event_type": "code_diagnostic_detected",
  "concept_tag": "array_indexing",
  "occurred_at": "2026-04-16T10:30:00Z",
  "payload": {}
}
```

### Response

```json
{
  "event_id": "4cc9938d-8be4-4c14-a9dc-333333333333",
  "status": "accepted"
}
```

## Code Coach Contracts

### 1. Analyze Code

This is the operational endpoint used by the extension.

#### Endpoint

`POST /api/v1/code-coach/analyze`

#### Request

```json
{
  "learning_session_id": "8c7f04cb-2b7a-41e0-8d44-222222222222",
  "task_id": "arrays_lab_01",
  "language": "java",
  "code": "class A { ... }",
  "enable_logging": true
}
```

#### Response

```json
{
  "status": "ok",
  "message": "Analysis completed.",
  "timestamp": "2026-04-16T10:30:00Z",
  "analysis_duration_ms": 84.1,
  "diagnostics": [
    {
      "diagnostic_id": "cc_34325868b926",
      "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
      "severity": "warning",
      "line": 8,
      "column": 21,
      "confidence": 0.99,
      "message": "Possible array index out-of-bounds issue detected.",
      "code_context": "arr[arr.length]",
      "concept_tag": "array_indexing",
      "explanation_key": "array_length_used_as_index",
      "status": "active",
      "detection_engine": "ml_gated_ast_locator",
      "ml_probability": 0.9996,
      "locator_confidence": 0.94,
      "hints": {
        "concept": "Array length tells you how many items exist, not the last valid position.",
        "guidance": "Compare the number of elements with the final usable index.",
        "targeted": "Check whether the array length is being used directly as an index."
      }
    }
  ]
}
```

### 2. Persist Diagnostic Event

Code Coach should publish a diagnostic event after successful analysis.

#### Event Type

`code_diagnostic_detected`

#### Payload

```json
{
  "diagnostic_id": "cc_34325868b926",
  "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
  "concept_tag": "array_indexing",
  "explanation_key": "array_length_used_as_index",
  "line": 8,
  "column": 21,
  "confidence": 0.99,
  "ml_probability": 0.9996,
  "locator_confidence": 0.94,
  "detection_engine": "ml_gated_ast_locator",
  "status": "active"
}
```

### 3. Hint Interaction Event

#### Event Types

- `hint_shown`
- `hint_level_requested`
- `hint_navigation_used`

#### Payload

```json
{
  "diagnostic_id": "cc_34325868b926",
  "hint_level": "guidance",
  "interaction_type": "shown"
}
```

### 4. Diagnostic Resolution Event

#### Event Type

`diagnostic_resolved`

#### Payload

```json
{
  "diagnostic_id": "cc_34325868b926",
  "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
  "concept_tag": "array_indexing",
  "resolved_at": "2026-04-16T10:35:04Z",
  "time_to_fix_seconds": 304
}
```

## Student Progress Tracker / Study Guider Contracts

This component mainly consumes Code Coach diagnostic signals and emits remediation signals.

### 1. Read User Diagnostic Summary

#### Endpoint

`GET /api/v1/users/{user_id}/diagnostic-summary`

#### Response Example

```json
{
  "user_id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
  "top_error_types": [
    {
      "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
      "count": 5,
      "last_seen_at": "2026-04-16T10:30:00Z"
    }
  ],
  "top_concepts": [
    {
      "concept_tag": "array_indexing",
      "repeat_count": 5,
      "unresolved_count": 2
    }
  ]
}
```

### 2. Read User Concept Struggles

#### Endpoint

`GET /api/v1/users/{user_id}/concept-struggles`

#### Response Example

```json
{
  "user_id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
  "struggles": [
    {
      "concept_tag": "array_indexing",
      "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
      "repeat_count": 3,
      "struggle_level": "high",
      "recommended_action": "trigger_study_guider"
    }
  ]
}
```

### 3. Publish Remediation Trigger

#### Event Type

`struggle_signal_created`

#### Payload

```json
{
  "concept_tag": "array_indexing",
  "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
  "repeat_count": 3,
  "struggle_level": "high",
  "reason": "three_consecutive_failures"
}
```

### 4. Publish Micro-Lesson Trigger

#### Event Type

`micro_lesson_triggered`

#### Payload

```json
{
  "concept_tag": "array_indexing",
  "trigger_source": "code_coach",
  "linked_error_type": "ARRAY_LENGTH_INDEX_MISUSE",
  "lesson_id": "lesson_arrays_01"
}
```

### 5. Read Study Guider Recommendations

#### Endpoint

`GET /api/v1/remediation/me/recommendations`

#### Response Example

```json
{
  "status": "ok",
  "message": "Study Guider recommendations generated from active remediation triggers.",
  "total": 1,
  "recommendations": [
    {
      "recommendation_id": "sgrec_123456789abc",
      "trigger_id": "rt_001",
      "trigger_source": "code_coach",
      "learning_session_id": "ls_001",
      "concept_tag": "array_indexing",
      "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
      "struggle_level": "high",
      "recommended_action": "trigger_study_guider",
      "lesson": {
        "lesson_id": "lesson_arrays_01",
        "title": "Array Indexing Basics"
      },
      "quiz": {
        "quiz_id": "quiz_arrays_01",
        "title": "Array Index Quiz"
      },
      "priority": "high"
    }
  ]
}
```

### 6. Record Micro-Lesson Opened

#### Endpoint

`POST /api/v1/remediation/me/triggers/{trigger_id}/lesson-opened`

#### Request Example

```json
{
  "lesson_id": "lesson_arrays_01"
}
```

#### Result

- updates the remediation trigger lifecycle
- emits `micro_lesson_viewed`

### 7. Record Quiz Completed

#### Endpoint

`POST /api/v1/remediation/me/triggers/{trigger_id}/quiz-completed`

#### Request Example

```json
{
  "quiz_id": "quiz_arrays_01",
  "score_percent": 84
}
```

#### Result

- updates the remediation trigger lifecycle
- marks the trigger completed when the quiz pass condition is met
- emits `quiz_completed`
- emits `mastery_updated`

## Adaptive Gamification Engine Contracts

This component should consume weakness signals and publish game outcomes.

### 1. Read Adaptive Gamification Recommendations

#### Endpoint

`GET /api/v1/gamification/me/recommendations`

#### Response Example

```json
{
  "status": "ok",
  "message": "Adaptive gamification recommendations generated from Code Coach struggle and mastery signals.",
  "total": 1,
  "recommendations": [
    {
      "recommendation_id": "grec_123456789abc",
      "concept_tag": "loop_boundaries",
      "error_type": "OFF_BY_ONE_LOOP_BOUNDARY",
      "recommendation_source": "concept_struggle",
      "adaptation_goal": "remediation",
      "based_on_struggle_level": "high",
      "game_id": "game_loops_trace_01",
      "game_type": "loop_tracer",
      "title": "Loop Boundary Trace",
      "difficulty_level": "beginner",
      "support_level": "high",
      "priority": "high"
    }
  ]
}
```

Useful supporting endpoints for the gamification component:

- `GET /api/v1/users/me/concept-struggles`
- `GET /api/v1/users/me/mastery`

### 2. Publish Game Session Result

#### Endpoint

`POST /api/v1/gamification/me/session-results`

#### Request Example

```json
{
  "learning_session_id": "ls_001",
  "concept_tag": "loop_boundaries",
  "game_id": "game_loops_trace_01",
  "game_type": "loop_tracer",
  "difficulty_level": "beginner",
  "score_percent": 78,
  "error_count": 2,
  "attempt_count": 2,
  "hint_usage": 1,
  "time_taken_seconds": 95,
  "support_level": "guided"
}
```

#### Result

- emits `game_session_completed`
- emits `mastery_updated`
- updates the student's `conceptMastery` snapshot for that concept

### 3. Publish Adaptation Decision

#### Endpoint

`POST /api/v1/gamification/me/adaptation-decisions`

#### Request Example

```json
{
  "learning_session_id": "ls_001",
  "concept_tag": "loop_boundaries",
  "recommendation_id": "grec_123456789abc",
  "game_id": "game_loops_trace_01",
  "game_type": "loop_tracer",
  "difficulty_level": "beginner",
  "support_level": "high",
  "rationale": "Repeated off-by-one issues need guided practice.",
  "based_on_struggle_level": "high"
}
```

#### Result

- emits `game_adaptation_decision_created`

## Collaborative Studio Contracts

This component should link collaboration and review activity to Code Coach signals.

### 1. Read Collaboration Prompts

#### Endpoint

`GET /api/v1/collaboration/me/prompts`

#### Response Example

```json
{
  "status": "ok",
  "message": "Collaborative prompts generated from Code Coach diagnostics, struggles, and mastery signals.",
  "total": 1,
  "prompts": [
    {
      "prompt_id": "cpr_123456789abc",
      "prompt_type": "reasoning_prompt",
      "collaboration_mode": "pair_programming",
      "concept_tag": "array_indexing",
      "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
      "linked_diagnostic_id": "cc_34325868b926",
      "title": "Reason About the Last Valid Index",
      "target_role": "navigator",
      "priority": "high"
    }
  ]
}
```

### 2. Publish Pair Session Start

#### Endpoint

`POST /api/v1/collaboration/me/pair-sessions`

#### Request Example

```json
{
  "learning_session_id": "ls_001",
  "collaboration_mode": "pair_programming",
  "partner_user_id": "6f9f5a6a-8f86-4b6c-baaa-444444444444",
  "task_id": "arrays_lab_01",
  "linked_learning_session_id": "ls_code_001"
}
```

#### Result

- creates a persistent collaboration session
- emits `pair_session_started`

### 3. Publish Collaboration Prompt Display

#### Endpoint

`POST /api/v1/collaboration/me/prompts/shown`

#### Request Example

```json
{
  "learning_session_id": "ls_001",
  "pair_session_id": "collab_001",
  "prompt_id": "cpr_123456789abc",
  "linked_diagnostic_id": "cc_34325868b926",
  "prompt_type": "reasoning_prompt",
  "concept_tag": "array_indexing",
  "linked_learning_session_id": "ls_code_001",
  "target_role": "navigator"
}
```

#### Result

- emits `collaboration_prompt_shown`

### 4. Publish Peer Review

#### Endpoint

`POST /api/v1/collaboration/me/peer-reviews`

#### Request Example

```json
{
  "learning_session_id": "ls_001",
  "pair_session_id": "collab_001",
  "concept_tag": "array_indexing",
  "linked_diagnostic_id": "cc_34325868b926",
  "linked_learning_session_id": "ls_code_001",
  "rubric_score": 4,
  "feedback_quality_score": 0.76,
  "review_comment": "The reviewer correctly explains the safe last index."
}
```

#### Result

- emits `peer_review_submitted`

## Mastery Contract

### Read Concept Mastery

#### Endpoint

`GET /api/v1/users/{user_id}/mastery`

Current authenticated Code Coach backend implementation:

`GET /api/v1/users/me/mastery`

#### Response Example

```json
{
  "user_id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
  "concepts": [
    {
      "concept_tag": "array_indexing",
      "mastery_score": 0.42,
      "struggle_score": 0.81,
      "last_updated_at": "2026-04-16T11:00:00Z"
    }
  ]
}
```

### Publish Mastery Update

#### Event Type

`mastery_updated`

#### Payload

```json
{
  "concept_tag": "array_indexing",
  "mastery_score": 0.58,
  "struggle_score": 0.63,
  "update_source": "quiz_completed"
}
```

## Dashboard Contracts

### 1. Read Dashboard Overview

#### Endpoint

`GET /api/v1/dashboard/me/overview`

#### Response Example

```json
{
  "status": "ok",
  "user_id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
  "counts": {
    "total_diagnostics": 4,
    "total_hint_events": 3,
    "total_game_sessions": 1,
    "total_pair_sessions": 1,
    "total_peer_reviews": 1
  },
  "mastery": {
    "total_concepts": 2,
    "strong_count": 1,
    "developing_count": 1,
    "at_risk_count": 0
  },
  "concept_trends": [
    {
      "concept_tag": "array_indexing",
      "active_count": 1,
      "struggle_level": "high",
      "recommended_focus": "study_guider_and_collaboration"
    }
  ]
}
```

### 2. Read Dashboard Timeline

#### Endpoint

`GET /api/v1/dashboard/me/timeline`

#### Response Example

```json
{
  "status": "ok",
  "user_id": "7c7b7d8d-6b27-4d80-a0f9-111111111111",
  "total": 3,
  "events": [
    {
      "event_type": "game_session_completed",
      "title": "Game completed"
    },
    {
      "event_type": "peer_review_submitted",
      "title": "Peer review submitted"
    }
  ]
}
```

## API Response Conventions

Recommended success envelope:

```json
{
  "status": "ok",
  "data": {}
}
```

Recommended error envelope:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "The request payload is missing required fields."
  }
}
```

## Idempotency and Reliability

For event ingestion:

- clients should send `X-Request-Id`
- backend should de-duplicate repeated event submissions when possible
- long-running downstream work should be handled asynchronously later if needed

For example:

- Code Coach returns analysis immediately
- event persistence happens in the same request or a background-safe queue later

## Access Control Rules

Recommended rules:

- students can read only their own learning profile
- lecturers can read enrolled student summaries
- components can publish only their own event types
- only approved services can update concept mastery summaries directly

## Versioning Strategy

Use endpoint versioning from the start:

- `/api/v1/...`

If payloads change later, prefer additive changes first. Avoid breaking field names unnecessarily because the VS Code extension and the web components will depend on them.

## Recommended First Implementation Slice

To reduce risk, integrate in this order:

1. auth token + shared user identity
2. learning session creation
3. Code Coach diagnostic persistence
4. shared event ingestion endpoint
5. user diagnostic summary endpoints
6. struggle signal endpoint for Study Guider
7. game result and collaboration event publishing

## Open Questions

These should be agreed before coding begins:

1. Will there be one backend monolith first, or separate services from the beginning?
2. Should event publishing be synchronous at first, or stored through an async queue?
3. Which component is responsible for creating `learning_session_id`?
4. Should pair programming sessions create one shared learning session or one per user plus a shared collaboration session?
5. Will lecturer dashboards read directly from summary endpoints or through a separate analytics service later?
