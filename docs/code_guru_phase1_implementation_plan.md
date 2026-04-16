# Code Guru Phase 1 Implementation Plan

This document defines the first implementation slice for Code Guru integration.

Phase 1 is intentionally narrow. It focuses only on:

1. authentication
2. `learningSessions`
3. Code Coach diagnostic persistence

The purpose of this phase is to make Code Coach data reliably belong to the correct logged-in user and become reusable by the other Code Guru components later.

## Related Docs

- [Code Guru Shared Data Model](C:/Hello/Tutorials/code-coach/docs/code_guru_shared_data_model.md)
- [Code Guru Integration API Contract](C:/Hello/Tutorials/code-coach/docs/code_guru_integration_api_contract.md)
- [Code Coach Proposal Traceability](C:/Hello/Tutorials/code-coach/docs/proposal_traceability.md)

## Phase 1 Goal

At the end of Phase 1, the system should be able to do this:

```text
Student logs in
-> VS Code extension gets authenticated context
-> a learning session is created or resumed
-> Code Coach analyzes code
-> diagnostics are saved in MongoDB under the correct user and session
-> the API can later query those saved diagnostics per user and per session
```

## Why This Phase Comes First

Without this phase:

- Code Coach remains mostly stateless
- other components cannot trust Code Coach data
- repeated-error analysis is hard
- Study Guider cannot know which student is struggling
- Gamification cannot personalize by user weakness
- Collaborative Studio cannot link diagnostics to pair activity

This phase creates the minimum shared learning identity layer.

## In Scope

### 1. Authentication

- basic student login
- JWT token generation and validation
- authenticated user resolution on backend requests
- role support for at least `student`

### 2. Learning Session Management

- create a `learningSession`
- resume an active session when appropriate
- attach Code Coach analysis to a session
- support at least VS Code as a client source

### 3. Code Coach Diagnostic Persistence

- save each returned diagnostic under the authenticated user and active learning session
- save metadata needed for later integration:
  - error type
  - concept tag
  - confidence
  - ML probability
  - locator confidence
  - line and column
  - diagnostic status
  - timestamp

### 4. Minimum Read APIs

- get current user profile
- get diagnostics for a user
- get diagnostics for a learning session

## Out of Scope

These are explicitly not part of Phase 1:

- full Study Guider remediation triggers
- concept mastery calculation
- gamification adaptation logic
- collaboration event tracking
- lecturer dashboard
- Neo4j integration
- raw code storage for analytics
- cross-component event bus

## Recommended Tech Decisions For Phase 1

### Backend

- keep the current FastAPI backend
- add MongoDB access there first instead of introducing a second backend immediately
- use environment variables:
  - `MONGODB_URI`
  - `MONGODB_DB_NAME=code-guru`
  - `JWT_SECRET`
  - `JWT_ALGORITHM`

### Database

Use MongoDB Atlas database:

```text
code-guru
```

Phase 1 collections:

- `users`
- `authSessions`
- `learningSessions`
- `codeDiagnostics`

Optional in late Phase 1 if useful:

- `hintInteractions`

## Phase 1 Architecture Slice

```text
VS Code Extension
   |
   +--> login request
   |
   +--> create/resume learning session
   |
   +--> analyze code request with JWT + learningSessionId
            |
            v
        FastAPI backend
            |
            +--> verify JWT
            +--> resolve userId
            +--> run Code Coach analysis
            +--> persist diagnostics in MongoDB
            +--> return diagnostics to extension
```

## Collection Design For Phase 1

### `users`

Purpose:

- stores student identity records

Suggested document:

```json
{
  "_id": { "$oid": "..." },
  "userId": "usr_001",
  "studentNumber": "IT22253958",
  "fullName": "Nethmina W P R",
  "email": "student@example.com",
  "role": "student",
  "passwordHash": "<hashed password>",
  "status": "active",
  "createdAt": "2026-04-16T10:00:00Z"
}
```

### `authSessions`

Purpose:

- records issued login sessions

Suggested document:

```json
{
  "_id": { "$oid": "..." },
  "authSessionId": "auth_001",
  "userId": "usr_001",
  "clientType": "vscode",
  "issuedAt": "2026-04-16T10:05:00Z",
  "expiresAt": "2026-04-16T11:05:00Z",
  "lastSeenAt": "2026-04-16T10:25:00Z",
  "status": "active"
}
```

### `learningSessions`

Purpose:

- groups a student's coding activity into a meaningful session

Suggested document:

```json
{
  "_id": { "$oid": "..." },
  "learningSessionId": "ls_001",
  "userId": "usr_001",
  "authSessionId": "auth_001",
  "sourceComponent": "code_coach",
  "clientType": "vscode",
  "taskId": "arrays_lab_01",
  "courseId": "SE4010",
  "language": "java",
  "status": "active",
  "startedAt": "2026-04-16T10:10:00Z",
  "endedAt": null,
  "lastAnalysisAt": "2026-04-16T10:25:00Z"
}
```

### `codeDiagnostics`

Purpose:

- stores persisted Code Coach diagnostic results

Suggested document:

```json
{
  "_id": { "$oid": "..." },
  "diagnosticRecordId": "diagrec_001",
  "diagnosticId": "cc_34325868b926",
  "userId": "usr_001",
  "learningSessionId": "ls_001",
  "errorType": "ARRAY_LENGTH_INDEX_MISUSE",
  "conceptTag": "array_indexing",
  "explanationKey": "array_length_used_as_index",
  "line": 8,
  "column": 21,
  "severity": "warning",
  "confidence": 0.99,
  "mlProbability": 0.9996,
  "locatorConfidence": 0.94,
  "detectionEngine": "ml_gated_ast_locator",
  "status": "active",
  "codeContextHash": "8b1a9953c4611296",
  "createdAt": "2026-04-16T10:25:00Z",
  "resolvedAt": null
}
```

## Required Indexes For Phase 1

Create these indexes early:

- `users: { userId: 1 }, unique`
- `users: { email: 1 }, unique`
- `authSessions: { authSessionId: 1 }, unique`
- `authSessions: { userId: 1, status: 1 }`
- `learningSessions: { learningSessionId: 1 }, unique`
- `learningSessions: { userId: 1, status: 1, startedAt: -1 }`
- `codeDiagnostics: { diagnosticRecordId: 1 }, unique`
- `codeDiagnostics: { userId: 1, createdAt: -1 }`
- `codeDiagnostics: { learningSessionId: 1, createdAt: -1 }`
- `codeDiagnostics: { userId: 1, errorType: 1, createdAt: -1 }`

## API Plan For Phase 1

### 1. Login

#### Endpoint

`POST /api/v1/auth/login`

#### Request

```json
{
  "email": "student@example.com",
  "password": "plain-text-password"
}
```

#### Response

```json
{
  "status": "ok",
  "data": {
    "accessToken": "<jwt>",
    "expiresIn": 3600,
    "user": {
      "userId": "usr_001",
      "studentNumber": "IT22253958",
      "fullName": "Nethmina W P R",
      "role": "student"
    }
  }
}
```

### 2. Get Current User

#### Endpoint

`GET /api/v1/auth/me`

#### Purpose

- allows extension or web UI to confirm login state

### 3. Create Learning Session

#### Endpoint

`POST /api/v1/sessions`

#### Request

```json
{
  "sourceComponent": "code_coach",
  "clientType": "vscode",
  "taskId": "arrays_lab_01",
  "courseId": "SE4010",
  "language": "java"
}
```

#### Response

```json
{
  "status": "ok",
  "data": {
    "learningSessionId": "ls_001",
    "status": "active"
  }
}
```

### 4. Resume Latest Active Learning Session

#### Endpoint

`GET /api/v1/sessions/active?sourceComponent=code_coach`

#### Purpose

- lets the VS Code extension reuse an active session instead of creating one every time

### 5. Analyze Code

#### Endpoint

`POST /api/v1/code-coach/analyze`

#### Request

```json
{
  "learningSessionId": "ls_001",
  "taskId": "arrays_lab_01",
  "language": "java",
  "code": "class A { ... }"
}
```

#### Required backend behavior

When this request arrives:

1. validate JWT
2. resolve authenticated `userId`
3. confirm the session belongs to the user
4. run Code Coach analysis
5. persist returned diagnostics to MongoDB
6. return the diagnostics to the extension

### 6. Get User Diagnostics

#### Endpoint

`GET /api/v1/diagnostics/me`

Optional filters:

- `learningSessionId`
- `errorType`
- `status`
- `limit`

### 7. Get Session Diagnostics

#### Endpoint

`GET /api/v1/sessions/{learningSessionId}/diagnostics`

## Backend Implementation Tasks

### Task Group A: Auth Foundation

1. add user model and MongoDB collection access
2. implement password hashing
3. implement login endpoint
4. implement JWT creation and validation
5. implement `/auth/me`
6. add auth dependency for protected routes

### Task Group B: MongoDB Access Layer

1. add MongoDB client initialization using `MONGODB_URI`
2. add collection getters:
   - `users`
   - `authSessions`
   - `learningSessions`
   - `codeDiagnostics`
3. add startup connectivity check
4. add indexes on startup or migration script

### Task Group C: Learning Sessions

1. define Pydantic request/response models
2. implement create session endpoint
3. implement get active session endpoint
4. add session ownership validation
5. update session `lastAnalysisAt` after analysis

### Task Group D: Code Coach Diagnostic Persistence

1. map current analyzer response into persisted diagnostic documents
2. compute `codeContextHash` from `code_context`
3. insert diagnostics under authenticated `userId` and `learningSessionId`
4. avoid duplicate inserts for the same `diagnosticId` if needed
5. add read endpoints for user/session diagnostics

## VS Code Extension Changes For Phase 1

No implementation yet, but these changes will be needed later.

### Minimum extension responsibilities

1. login flow or token input flow
2. store JWT securely for the session
3. request or reuse a `learningSessionId`
4. send JWT and `learningSessionId` with analyze requests
5. handle auth expiration gracefully

### Temporary prototype option

If full login UI is too large for the first pass, a temporary bootstrap option is acceptable:

- manual token paste in extension setting
- session created after first successful authenticated call

This is acceptable for a prototype, but real login is the cleaner final path.

## Acceptance Criteria

Phase 1 is complete when all of these are true:

1. a student can authenticate successfully
2. authenticated requests resolve the correct `userId`
3. a learning session can be created and read back
4. Code Coach analysis can only persist diagnostics for the session owner
5. diagnostics are stored in MongoDB with:
   - `userId`
   - `learningSessionId`
   - `diagnosticId`
   - `errorType`
   - `conceptTag`
   - `confidence`
   - `mlProbability`
   - `locatorConfidence`
6. saved diagnostics can be queried per user and per session
7. no MongoDB secret is hardcoded in the repository

## Testing Plan For Phase 1

### Unit Tests

- password hashing and verification
- JWT validation
- session ownership checks
- diagnostic persistence mapping

### Integration Tests

- login -> create session -> analyze -> persisted diagnostics
- unauthorized analyze request is rejected
- analyze with wrong `learningSessionId` is rejected
- diagnostics query returns only the correct user's data

### Manual Test Scenario

```text
Login as student A
-> create learning session
-> analyze code containing ARRAY_LENGTH_INDEX_MISUSE
-> confirm diagnostic appears in MongoDB under student A
-> login as student B
-> confirm student B cannot read student A diagnostics
```

## Risks In Phase 1

### Risk 1: Too much auth complexity too early

Mitigation:

- implement only student login first
- keep role logic simple

### Risk 2: Session duplication

Mitigation:

- add a clear rule for active-session reuse
- reuse the newest active Code Coach session when appropriate

### Risk 3: Duplicate diagnostic writes

Mitigation:

- use a unique diagnostic record id
- optionally de-duplicate by `userId + learningSessionId + diagnosticId + status`

### Risk 4: Secret leakage

Mitigation:

- keep `MONGODB_URI` only in env configuration
- never commit the Atlas URI

## Recommended Build Order

Implement in this order:

1. MongoDB client and collections
2. user model and login
3. JWT protection
4. learning session endpoints
5. diagnostic persistence after analyze
6. read APIs for saved diagnostics
7. extension auth/session wiring

## Deliverables At The End Of Phase 1

1. authenticated backend endpoints
2. MongoDB collections for:
   - `users`
   - `authSessions`
   - `learningSessions`
   - `codeDiagnostics`
3. persisted Code Coach diagnostics tied to user and session
4. basic read APIs for future components
5. updated architecture documentation

## What Phase 2 Should Build On Top

Once Phase 1 is stable, Phase 2 should add:

- `learningEvents`
- `hintInteractions`
- repeated diagnostic detection
- first struggle signal generation
- Study Guider integration entry point
