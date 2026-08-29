# Code Coach — API Contract

> Generated from the running service by `python -m app.dev_tools.export_api_contract`.
> Every field below comes from the actual request/response models, so this file
> cannot drift from the implementation. Regenerate after any route change.

## Base URL

| Environment | URL |
|---|---|
| Local development | `http://127.0.0.1:8000` |
| Production (Cloud Run) | _added after deployment_ |

Interactive docs (try any endpoint in a browser): `<base>/docs`

## How to call this API

1. **Sign the student in** with `POST /api/v1/auth/login`. Keep the returned
   `access_token` (valid 1 hour) and `refresh_token`.
2. **Send the access token** on every request:
   `Authorization: Bearer <access_token>`.
3. **On HTTP 401**, call `POST /api/v1/auth/refresh` with the refresh token,
   then retry the original request once. Refresh tokens rotate: store the new
   one and discard the old.
4. **To validate a token your own service received**, forward it to
   `GET /api/v1/auth/me`. A `200` returns the verified user; a `401` means
   reject the request. Never ask students for their password in your own UI.

## Conventions

- All requests and responses are JSON; all timestamps are ISO-8601 UTC.
- `me` in a path always means "the user identified by the bearer token" —
  you cannot read another student's data, and no user id needs to be passed.
- Errors return `{"detail": "human readable reason"}` with a standard status:
  `400` bad request · `401` invalid/expired token · `403` inactive account ·
  `404` not found or not yours · `409` conflict · `422` validation failed ·
  `429` too many attempts (respect the `Retry-After` header).
- Browser clients must be on the CORS allow-list — send your dev origin
  (e.g. `http://localhost:3000`) to the Code Coach owner to have it added.
  Server-to-server calls are unaffected.
- The first request after an idle period may take a few seconds while the
  deployed container starts. Do not set aggressive client timeouts.

---

## Authentication (every service)

One account for the whole platform. Sign in through Code Coach, then send the returned access token on every request to any service. To validate a token your service receives, call GET /api/v1/auth/me with it.

### `POST /api/v1/auth/register`

Register

Auth: none required

Request body:

```json
{
  "full_name": "string",
  "email": "student@example.com",
  "password": "string",
  "client_name": "code-coach-vscode"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "user": {
    "user_id": "string",
    "full_name": "string",
    "email": "student@example.com",
    "role": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z"
  },
  "auth_session": {
    "auth_session_id": "string",
    "client_name": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z",
    "last_seen_at": "2026-07-12T10:22:41Z",
    "expires_at": "2026-07-12T10:22:41Z"
  },
  "tokens": {
    "token_type": "Bearer",
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 0
  }
}
```

### `POST /api/v1/auth/login`

Login

Auth: none required

Request body:

```json
{
  "identifier": "string",
  "password": "string",
  "client_name": "code-coach-vscode"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "user": {
    "user_id": "string",
    "full_name": "string",
    "email": "student@example.com",
    "role": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z"
  },
  "auth_session": {
    "auth_session_id": "string",
    "client_name": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z",
    "last_seen_at": "2026-07-12T10:22:41Z",
    "expires_at": "2026-07-12T10:22:41Z"
  },
  "tokens": {
    "token_type": "Bearer",
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 0
  }
}
```

### `POST /api/v1/auth/refresh`

Refresh

Auth: none required

Request body:

```json
{
  "refresh_token": "string"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "user": {
    "user_id": "string",
    "full_name": "string",
    "email": "student@example.com",
    "role": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z"
  },
  "auth_session": {
    "auth_session_id": "string",
    "client_name": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z",
    "last_seen_at": "2026-07-12T10:22:41Z",
    "expires_at": "2026-07-12T10:22:41Z"
  },
  "tokens": {
    "token_type": "Bearer",
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 0
  }
}
```

### `POST /api/v1/auth/logout`

Logout

Auth: `Authorization: Bearer <access_token>`

Response `200`:

```json
{
  "status": "string",
  "message": "string"
}
```

### `GET /api/v1/auth/me`

Me

Auth: `Authorization: Bearer <access_token>`

Response `200`:

```json
{
  "status": "string",
  "user": {
    "user_id": "string",
    "full_name": "string",
    "email": "student@example.com",
    "role": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z"
  },
  "auth_session": {
    "auth_session_id": "string",
    "client_name": "string",
    "status": "string",
    "created_at": "2026-07-12T10:22:41Z",
    "last_seen_at": "2026-07-12T10:22:41Z",
    "expires_at": "2026-07-12T10:22:41Z"
  }
}
```

---

## Learning sessions (every service)

A learning session groups a student's activity. Create or reuse one before submitting analysis or events.

### `POST /api/v1/learning-sessions`

Create Or Resume Learning Session

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "source_component": "code_coach",
  "language": "java",
  "task_id": "string"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "learning_session_id": "string",
  "user_id": "string",
  "source_component": "string",
  "language": "string",
  "task_id": "string",
  "learning_session_status": "string",
  "started_at": "2026-07-12T10:22:41Z",
  "last_analysis_at": "2026-07-12T10:22:41Z",
  "reused_existing": false
}
```

### `GET /api/v1/learning-sessions/{learning_session_id}`

Get Learning Session

Auth: `Authorization: Bearer <access_token>`

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "learning_session_id": "string",
  "user_id": "string",
  "source_component": "string",
  "language": "string",
  "task_id": "string",
  "learning_session_status": "string",
  "started_at": "2026-07-12T10:22:41Z",
  "last_analysis_at": "2026-07-12T10:22:41Z",
  "reused_existing": false
}
```

### `GET /api/v1/learning-sessions/{learning_session_id}/diagnostics`

Get Learning Session Diagnostics

Auth: `Authorization: Bearer <access_token>`

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "diagnostics": [
    {
      "diagnostic_record_id": "...",
      "diagnostic_id": "...",
      "user_id": "...",
      "learning_session_id": "...",
      "error_type": "...",
      "concept_tag": "...",
      "explanation_key": "...",
      "line": "...",
      "column": "...",
      "severity": "...",
      "confidence": "...",
      "ml_probability": "...",
      "locator_confidence": "...",
      "detection_engine": "...",
      "status": "...",
      "code_context_hash": "...",
      "created_at": "...",
      "resolved_at": "..."
    }
  ]
}
```

---

## Student data (Study Guider · Gamification · Website)

Everything Code Coach knows about the signed-in student. 'me' always means the user identified by the bearer token.

### `GET /api/v1/students/me/diagnostics`

Get My Diagnostics

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `learning_session_id`
- `error_type`
- `status`
- `limit` (default `50`, range 1–200)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "diagnostics": [
    {
      "diagnostic_record_id": "...",
      "diagnostic_id": "...",
      "user_id": "...",
      "learning_session_id": "...",
      "error_type": "...",
      "concept_tag": "...",
      "explanation_key": "...",
      "line": "...",
      "column": "...",
      "severity": "...",
      "confidence": "...",
      "ml_probability": "...",
      "locator_confidence": "...",
      "detection_engine": "...",
      "status": "...",
      "code_context_hash": "...",
      "created_at": "...",
      "resolved_at": "..."
    }
  ]
}
```

### `GET /api/v1/students/me/diagnostics/summary`

Get My Diagnostics Summary

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `5`, range 1–20)
- `sample_size` (default `200`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "user_id": "string",
  "total_diagnostics": 0,
  "total_hint_events": 0,
  "concepts_with_hint_usage": 0,
  "top_error_types": [
    {
      "error_type": "...",
      "count": "...",
      "active_count": "...",
      "last_seen_at": "..."
    }
  ],
  "top_concepts": [
    {
      "concept_tag": "...",
      "repeat_count": "...",
      "unresolved_count": "...",
      "last_seen_at": "...",
      "hint_event_count": "...",
      "hint_shown_count": "...",
      "hint_request_count": "...",
      "hint_navigation_count": "...",
      "hint_dependency_score": "...",
      "hint_dependency_level": "...",
      "last_hint_at": "..."
    }
  ]
}
```

### `GET /api/v1/students/me/struggling-concepts`

Get My Struggling Concepts

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `10`, range 1–20)
- `sample_size` (default `200`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "user_id": "string",
  "total_concepts": 0,
  "struggles": [
    {
      "concept_tag": "...",
      "error_type": "...",
      "repeat_count": "...",
      "active_count": "...",
      "resolved_count": "...",
      "unique_learning_sessions": "...",
      "last_seen_at": "...",
      "hint_event_count": "...",
      "hint_shown_count": "...",
      "hint_request_count": "...",
      "hint_navigation_count": "...",
      "hint_dependency_score": "...",
      "hint_dependency_level": "...",
      "last_hint_at": "...",
      "struggle_score": "...",
      "struggle_level": "...",
      "recommended_action": "..."
    }
  ]
}
```

### `GET /api/v1/students/me/concept-mastery`

Get My Concept Mastery

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `20`, range 1–50)

Response `200`:

```json
{
  "status": "string",
  "user_id": "string",
  "total_concepts": 0,
  "concepts": [
    {
      "concept_tag": "...",
      "mastery_score": "...",
      "struggle_score": "...",
      "mastery_level": "...",
      "update_source": "...",
      "last_learning_session_id": "...",
      "last_error_type": "...",
      "last_trigger_id": "...",
      "last_quiz_id": "...",
      "last_quiz_score_percent": "...",
      "last_quiz_passed": "...",
      "last_game_id": "...",
      "last_game_type": "...",
      "last_game_score_percent": "...",
      "last_game_difficulty_level": "...",
      "last_updated_at": "..."
    }
  ]
}
```

---

## Remediation (Study Guider)

Struggle triggers raised by Code Coach, and the callbacks Study Guider uses to report lesson and quiz progress back.

### `GET /api/v1/remediation/me/triggers`

Get My Remediation Triggers

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `status`
- `trigger_source`
- `limit` (default `50`, range 1–200)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "triggers": [
    {
      "trigger_id": "...",
      "user_id": "...",
      "learning_session_id": "...",
      "trigger_source": "...",
      "concept_tag": "...",
      "error_type": "...",
      "reason": "...",
      "struggle_level": "...",
      "recommended_action": "...",
      "repeat_count": "...",
      "active_count": "...",
      "resolved_count": "...",
      "unique_learning_sessions": "...",
      "struggle_score": "...",
      "hint_dependency_score": "...",
      "hint_dependency_level": "...",
      "status": "...",
      "intervention_status": "...",
      "lesson_id": "...",
      "lesson_opened_at": "...",
      "quiz_id": "...",
      "quiz_completed_at": "...",
      "quiz_score_percent": "...",
      "quiz_passed": "...",
      "created_at": "...",
      "updated_at": "...",
      "resolved_at": "..."
    }
  ]
}
```

### `GET /api/v1/remediation/me/recommendations`

Get My Study Guider Recommendations

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `50`, range 1–200)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "recommendations": [
    {
      "recommendation_id": "...",
      "trigger_id": "...",
      "trigger_source": "...",
      "learning_session_id": "...",
      "concept_tag": "...",
      "error_type": "...",
      "struggle_level": "...",
      "recommended_action": "...",
      "lesson": "...",
      "quiz": "...",
      "rationale": "...",
      "priority": "..."
    }
  ]
}
```

### `POST /api/v1/remediation/me/triggers/{trigger_id}/lesson-opened`

Mark Lesson Opened

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "lesson_id": "string",
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "trigger": {
    "trigger_id": "string",
    "user_id": "string",
    "learning_session_id": "string",
    "trigger_source": "string",
    "concept_tag": "string",
    "error_type": "string",
    "reason": "string",
    "struggle_level": "string",
    "recommended_action": "string",
    "repeat_count": 0,
    "active_count": 0,
    "resolved_count": 0,
    "unique_learning_sessions": 0,
    "struggle_score": 0.0,
    "hint_dependency_score": 0.0,
    "hint_dependency_level": "low",
    "status": "string",
    "intervention_status": "pending",
    "lesson_id": "string",
    "lesson_opened_at": "2026-07-12T10:22:41Z",
    "quiz_id": "string",
    "quiz_completed_at": "2026-07-12T10:22:41Z",
    "quiz_score_percent": 0,
    "quiz_passed": false,
    "created_at": "2026-07-12T10:22:41Z",
    "updated_at": "2026-07-12T10:22:41Z",
    "resolved_at": "2026-07-12T10:22:41Z"
  },
  "created_event_types": [
    "string"
  ]
}
```

### `POST /api/v1/remediation/me/triggers/{trigger_id}/quiz-completed`

Mark Quiz Completed

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "quiz_id": "string",
  "score_percent": 0,
  "passed": false,
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "trigger": {
    "trigger_id": "string",
    "user_id": "string",
    "learning_session_id": "string",
    "trigger_source": "string",
    "concept_tag": "string",
    "error_type": "string",
    "reason": "string",
    "struggle_level": "string",
    "recommended_action": "string",
    "repeat_count": 0,
    "active_count": 0,
    "resolved_count": 0,
    "unique_learning_sessions": 0,
    "struggle_score": 0.0,
    "hint_dependency_score": 0.0,
    "hint_dependency_level": "low",
    "status": "string",
    "intervention_status": "pending",
    "lesson_id": "string",
    "lesson_opened_at": "2026-07-12T10:22:41Z",
    "quiz_id": "string",
    "quiz_completed_at": "2026-07-12T10:22:41Z",
    "quiz_score_percent": 0,
    "quiz_passed": false,
    "created_at": "2026-07-12T10:22:41Z",
    "updated_at": "2026-07-12T10:22:41Z",
    "resolved_at": "2026-07-12T10:22:41Z"
  },
  "created_event_types": [
    "string"
  ]
}
```

---

## Gamification engine

Recommendation and result endpoints for adaptive practice.

### `GET /api/v1/gamification/me/recommendations`

Get My Gamification Recommendations

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `10`, range 1–25)
- `sample_size` (default `200`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "recommendations": [
    {
      "recommendation_id": "...",
      "concept_tag": "...",
      "error_type": "...",
      "recommendation_source": "...",
      "adaptation_goal": "...",
      "based_on_mastery_level": "...",
      "based_on_struggle_level": "...",
      "game_id": "...",
      "game_type": "...",
      "title": "...",
      "difficulty_level": "...",
      "support_level": "...",
      "estimated_duration_minutes": "...",
      "focus_points": "...",
      "rationale": "...",
      "priority": "..."
    }
  ]
}
```

### `POST /api/v1/gamification/me/adaptation-decisions`

Create My Gamification Adaptation Decision

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "concept_tag": "string",
  "recommendation_id": "string",
  "game_id": "string",
  "game_type": "string",
  "difficulty_level": "string",
  "support_level": "string",
  "rationale": "string",
  "based_on_mastery_level": "string",
  "based_on_struggle_level": "string",
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "created_event_types": [
    "string"
  ],
  "mastery": {
    "concept_tag": "string",
    "mastery_score": 0.0,
    "struggle_score": 0.0,
    "mastery_level": "string",
    "update_source": "string",
    "last_learning_session_id": "string",
    "last_error_type": "string",
    "last_trigger_id": "string",
    "last_quiz_id": "string",
    "last_quiz_score_percent": 0,
    "last_quiz_passed": false,
    "last_game_id": "string",
    "last_game_type": "string",
    "last_game_score_percent": 0,
    "last_game_difficulty_level": "string",
    "last_updated_at": "2026-07-12T10:22:41Z"
  }
}
```

### `POST /api/v1/gamification/me/session-results`

Create My Gamification Session Result

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "concept_tag": "string",
  "recommendation_id": "string",
  "game_id": "string",
  "game_type": "string",
  "difficulty_level": "string",
  "support_level": "string",
  "score_percent": 0,
  "error_count": 0,
  "attempt_count": 0,
  "hint_usage": 0,
  "time_taken_seconds": 0,
  "passed": false,
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "created_event_types": [
    "string"
  ],
  "mastery": {
    "concept_tag": "string",
    "mastery_score": 0.0,
    "struggle_score": 0.0,
    "mastery_level": "string",
    "update_source": "string",
    "last_learning_session_id": "string",
    "last_error_type": "string",
    "last_trigger_id": "string",
    "last_quiz_id": "string",
    "last_quiz_score_percent": 0,
    "last_quiz_passed": false,
    "last_game_id": "string",
    "last_game_type": "string",
    "last_game_score_percent": 0,
    "last_game_difficulty_level": "string",
    "last_updated_at": "2026-07-12T10:22:41Z"
  }
}
```

---

## Collaboration (PairPath)

Pairing prompts derived from struggle signals, plus session and peer-review records.

### `GET /api/v1/collaboration/me/prompts`

Get My Collaboration Prompts

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `10`, range 1–25)
- `sample_size` (default `200`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "prompts": [
    {
      "prompt_id": "...",
      "prompt_type": "...",
      "collaboration_mode": "...",
      "concept_tag": "...",
      "error_type": "...",
      "linked_diagnostic_id": "...",
      "linked_learning_session_id": "...",
      "title": "...",
      "prompt_text": "...",
      "target_role": "...",
      "based_on_struggle_level": "...",
      "based_on_mastery_level": "...",
      "priority": "...",
      "rationale": "..."
    }
  ]
}
```

### `POST /api/v1/collaboration/me/prompts/shown`

Mark My Collaboration Prompt Shown

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "pair_session_id": "string",
  "prompt_id": "string",
  "prompt_type": "string",
  "concept_tag": "string",
  "linked_diagnostic_id": "string",
  "linkedLearningSessionId": "string",
  "target_role": "string",
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "pair_session_id": "string",
  "created_event_types": [
    "string"
  ]
}
```

### `POST /api/v1/collaboration/me/pair-sessions`

Create My Pair Session

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "collaboration_mode": "pair_programming",
  "partner_user_id": "string",
  "task_id": "string",
  "linkedLearningSessionId": "string"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "session": {
    "pair_session_id": "string",
    "user_id": "string",
    "learning_session_id": "string",
    "collaboration_mode": "string",
    "partner_user_id": "string",
    "task_id": "string",
    "linked_learning_session_id": "string",
    "status": "string",
    "started_at": "2026-07-12T10:22:41Z",
    "last_activity_at": "2026-07-12T10:22:41Z"
  },
  "created_event_types": [
    "string"
  ]
}
```

### `POST /api/v1/collaboration/me/peer-reviews`

Submit My Peer Review

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "pair_session_id": "string",
  "concept_tag": "string",
  "linked_diagnostic_id": "string",
  "linkedLearningSessionId": "string",
  "rubric_score": 0,
  "feedback_quality_score": 0.0,
  "review_comment": "string",
  "occurred_at": "2026-07-12T10:22:41Z"
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "pair_session_id": "string",
  "created_event_types": [
    "string"
  ]
}
```

---

## Dashboard (Website)

Pre-aggregated views for the student home page.

### `GET /api/v1/dashboard/me/overview`

Get My Dashboard Overview

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `concept_limit` (default `6`, range 1–20)
- `timeline_limit` (default `12`, range 1–50)
- `sample_size` (default `300`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "user_id": "string",
  "counts": {
    "total_diagnostics": 0,
    "active_diagnostics": 0,
    "resolved_diagnostics": 0,
    "total_hint_events": 0,
    "active_remediation_triggers": 0,
    "completed_remediation_triggers": 0,
    "total_game_sessions": 0,
    "total_pair_sessions": 0,
    "total_peer_reviews": 0,
    "total_lessons_viewed": 0,
    "total_quizzes_completed": 0
  },
  "mastery": {
    "total_concepts": 0,
    "strong_count": 0,
    "developing_count": 0,
    "at_risk_count": 0
  },
  "concept_trends": [
    {
      "concept_tag": "...",
      "repeat_count": "...",
      "active_count": "...",
      "struggle_level": "...",
      "mastery_level": "...",
      "mastery_score": "...",
      "hint_dependency_level": "...",
      "last_activity_at": "...",
      "recommended_focus": "..."
    }
  ],
  "recent_timeline": [
    {
      "event_id": "...",
      "component": "...",
      "event_type": "...",
      "title": "...",
      "summary": "...",
      "concept_tag": "...",
      "occurred_at": "..."
    }
  ]
}
```

### `GET /api/v1/dashboard/me/timeline`

Get My Dashboard Timeline

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `limit` (default `25`, range 1–100)
- `sample_size` (default `300`, range 1–1000)

Response `200`:

```json
{
  "status": "string",
  "user_id": "string",
  "total": 0,
  "events": [
    {
      "event_id": "...",
      "component": "...",
      "event_type": "...",
      "title": "...",
      "summary": "...",
      "concept_tag": "...",
      "occurred_at": "..."
    }
  ]
}
```

---

## Learning events (every service)

The shared activity log. Emit an event whenever a student interacts with your component; read them back for analytics.

### `POST /api/v1/events`

Create Learning Event

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "learningSessionId": "string",
  "component": "code_coach",
  "event_type": "string",
  "concept_tag": "string",
  "occurred_at": "2026-07-12T10:22:41Z",
  "payload": {}
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "event_id": "string"
}
```

### `GET /api/v1/events/me`

Get My Learning Events

Auth: `Authorization: Bearer <access_token>`

Query parameters:

- `learning_session_id`
- `event_type`
- `limit` (default `50`, range 1–200)

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "total": 0,
  "events": [
    {
      "event_id": "...",
      "user_id": "...",
      "learning_session_id": "...",
      "component": "...",
      "event_type": "...",
      "concept_tag": "...",
      "occurred_at": "...",
      "created_at": "...",
      "payload": "..."
    }
  ]
}
```

---

## Code analysis (Code Coach internal)

Used by the VS Code extension. Included for completeness.

### `POST /api/v1/code-coach/analyze`

Analyze For Authenticated User

Auth: `Authorization: Bearer <access_token>`

Request body:

```json
{
  "language": "string",
  "code": "string",
  "session_id": "string",
  "learningSessionId": "string",
  "enable_logging": false
}
```

Response `200`:

```json
{
  "status": "string",
  "message": "string",
  "timestamp": "string",
  "analysis_duration_ms": 0.0,
  "learning_session_id": "string",
  "diagnostics": [
    {
      "diagnostic_id": "...",
      "error_type": "...",
      "severity": "...",
      "line": "...",
      "column": "...",
      "confidence": "...",
      "message": "...",
      "code_context": "...",
      "concept_tag": "...",
      "explanation_key": "...",
      "status": "...",
      "detection_engine": "...",
      "ml_probability": "...",
      "locator_confidence": "...",
      "hints": "..."
    }
  ]
}
```

---

## Service health

No authentication required.

### `GET /health`

Health

Auth: none required

Response `200`:

```json
"..."
```

---
