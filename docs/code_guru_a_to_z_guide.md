# Code Guru A to Z Guide

This document gives the full picture of the **Code Guru** project in simple but detailed English.

It is written to help:

- understand the whole project clearly
- explain the project to teammates and supervisors
- show how **Code Coach** connects to the other components
- identify what data must be stored in the database
- support report writing or PDF creation later

---

## 1. What Is Code Guru?

**Code Guru** is an intelligent educational programming support platform for beginner programmers.

Its main purpose is not just to detect coding mistakes. Its bigger purpose is to:

- help beginners understand why they made mistakes
- keep them motivated while learning
- support collaboration with peers
- intervene with deeper lessons when students keep struggling

In simple words, Code Guru is trying to become a **complete beginner programming support ecosystem**.

Instead of giving students only compiler errors or AI-generated answers, Code Guru tries to give:

- immediate guidance
- practice
- collaboration support
- deeper remediation

That is why the project is divided into **four connected components**.

---

## 2. The Four Main Components

Code Guru has four major components:

1. **Code Coach**
2. **Adaptive Gamification Engine**
3. **Collaborative Pair Programming and Peer Review Studio**
4. **Student Progress Tracker / Study Guider**

Each component solves a different part of the beginner programming problem.

### 2.1 Code Coach

Code Coach is the **real-time coding support component**.

It works inside the coding environment and helps students while they are writing code.

Its job is to:

- detect beginner coding mistakes
- identify where the mistake is
- classify the mistake type
- give beginner-friendly hints
- save diagnostic data for the logged-in user

Code Coach is very important because it produces the first learning signals that other components can use.

### 2.2 Adaptive Gamification Engine

This component keeps students engaged by giving game-based learning activities.

Its job is to:

- choose a suitable game type
- adjust difficulty
- track performance in games
- provide extra practice for weak concepts

The proposal says it uses three main games:

- Drag and Drop Code Game
- Bug Hunt Game
- Code Trace Game

### 2.3 Collaborative Pair Programming and Peer Review Studio

This component supports learning through collaboration.

Its job is to:

- support structured pair programming
- support guided peer review
- monitor collaboration quality
- detect participation imbalance or weak communication
- provide pedagogical prompts to improve collaboration

### 2.4 Student Progress Tracker / Study Guider

This component is the **deep remediation and intervention layer**.

Its job is to:

- monitor long-term struggle patterns
- detect when a student is repeatedly failing the same concept
- trigger micro-lessons
- track concept mastery
- validate understanding through quizzes

This component is the system that decides:

> "This student is not just making a one-time mistake. This student is struggling and needs deeper support."

---

## 3. The Core Educational Idea Behind Code Guru

The main idea of Code Guru is:

```text
Immediate coding help
-> practice support
-> collaboration support
-> deep remediation when repeated struggle is detected
```

This means the platform does not treat every mistake equally.

For example:

- if the student makes one small mistake, Code Coach gives a hint
- if the student keeps making similar mistakes, the Gamification Engine can give targeted practice
- if the student is working with a partner, the Collaborative Studio can guide the collaboration
- if the student still keeps struggling, Study Guider can trigger a micro-lesson and quiz

So the platform works like a layered support system.

---

## 4. Why Code Coach Is the Mainstream Component

In your project, **Code Coach is the mainstream component** because it is the first place where coding struggles are captured.

This means Code Coach is the system that notices:

- what kind of coding mistake happened
- where it happened
- how often it happened
- whether it was resolved
- which programming concept is involved

Without Code Coach:

- Study Guider does not know which concept the student is failing
- Gamification does not know what kind of practice the student needs
- Collaborative Studio does not know what kind of pedagogical prompt to show

So Code Coach is not just a hinting system.

It is also the **diagnostic signal provider** for the whole platform.

---

## 5. Current Scope of Code Coach

For now, Code Coach is intentionally limited to **three beginner error types**.

These are the error types you are implementing right now:

1. `OFF_BY_ONE_LOOP_BOUNDARY`
2. `INCORRECT_CONDITIONAL_OPERATOR`
3. `ARRAY_LENGTH_INDEX_MISUSE`

### 5.1 OFF_BY_ONE_LOOP_BOUNDARY

This happens when a loop goes one step too far or stops one step too early.

Example:

```java
for (int i = 0; i <= arr.length; i++) {
    System.out.println(arr[i]);
}
```

Problem:

- `arr.length` is the number of elements
- the last valid array index is `arr.length - 1`
- using `<= arr.length` makes the loop go out of range

Concept involved:

- loop boundaries
- valid array index range

### 5.2 INCORRECT_CONDITIONAL_OPERATOR

This happens when the student uses assignment inside a condition instead of a comparison or a proper boolean condition.

Example:

```java
if (ready = true) {
    System.out.println("Ready");
}
```

Problem:

- `=` means assignment
- in many beginner cases, the student actually meant comparison or a boolean check

Concept involved:

- conditional expressions
- boolean logic
- operator meaning

### 5.3 ARRAY_LENGTH_INDEX_MISUSE

This happens when the student uses `array.length` directly as an index.

Example:

```java
System.out.println(arr[arr.length]);
```

Problem:

- `arr.length` is not the last valid index
- the last valid index is `arr.length - 1`

Concept involved:

- array indexing
- array length vs last index

---

## 6. How Code Coach Works From A to Z

This section explains the full Code Coach workflow.

## 6.1 High-Level Workflow

```text
Student logs in
-> opens Java file in VS Code
-> Code Coach extension watches code changes
-> extension sends code to backend
-> backend parses Java code
-> backend extracts features
-> ML predicts whether the 3 target errors are likely present
-> AST locator finds exact line/column
-> hints are generated
-> diagnostics are shown in VS Code
-> diagnostics are saved in MongoDB for that user and learning session
```

## 6.2 Step-by-Step Code Coach Workflow

### Step 1: User logs in

The student signs in through the VS Code extension.

The backend returns:

- access token
- refresh token
- user identity
- auth session information

Why this matters:

- all saved data must belong to a real logged-in user
- later components need user-linked data

### Step 2: Learning session is created or reused

When the student starts coding, the extension creates or reuses a `learningSession`.

A learning session represents:

- one student
- one coding context
- one component
- one task or coding activity

This is important because we do not want isolated diagnostics without context.

### Step 3: Student writes code

The VS Code extension watches Java files.

When the student pauses typing, the extension sends the latest code snapshot to the backend.

This is currently:

- **debounced real-time snapshot analysis**

This means:

- the system waits briefly after typing
- then analyzes the latest whole file

### Step 4: Backend parses the code

The backend uses **Tree-sitter** to parse Java code.

Tree-sitter builds an **AST**.

AST means **Abstract Syntax Tree**.

An AST is a structured tree representation of code.

Example:

Instead of treating code as plain text, the AST understands things like:

- loops
- conditions
- assignments
- array accesses

This is important because Code Coach needs structured code understanding.

### Step 5: Feature extraction

The backend extracts features from the code.

These features help the ML model decide whether one of the three target errors is likely present.

Examples of features:

- loop comparison operators
- array index expressions
- assignments inside conditions
- structural patterns in the code

### Step 6: ML prediction

Code Coach currently uses an **ML-led hybrid approach**.

This means:

- ML decides whether a target error type is likely present
- AST rules then find the exact location

So the ML model does not directly predict the exact line number.

Instead, it answers:

> "This file probably contains this beginner error type."

Then the AST locator answers:

> "This is the exact line and column where that error appears."

### Step 7: AST localization

If the ML model predicts a target error above the confidence threshold:

- the related locator runs
- the exact line and column are found
- code context is extracted

This gives a precise diagnostic for the editor.

### Step 8: Hint generation

After localization, Code Coach generates three levels of beginner-friendly hints:

- `concept`
- `guidance`
- `targeted`

Example:

- Concept hint: explains the idea
- Guidance hint: nudges the student
- Targeted hint: points near the issue without giving the full answer

### Step 9: VS Code display

The extension displays:

- inline diagnostics
- editor highlighting
- hover information
- output panel details
- hint navigation

### Step 10: Persistence in MongoDB

The diagnostic is saved in MongoDB under:

- the authenticated user
- the current learning session

This is the step that makes Code Coach useful for the other components.

### Step 11: Later re-use by other components

After saving the diagnostic, the system can later use it to answer questions like:

- Has this student repeated the same error many times?
- Which concept is weakest for this student?
- Which game should be recommended?
- Should a micro-lesson be triggered?
- What collaboration support prompt should be shown?

---

## 7. What Is Stored in the Database?

Code Guru currently uses **MongoDB Atlas** as the shared application database.

Database name:

```text
code-guru
```

For Phase 1 and integration planning, the important collections are:

- `users`
- `authSessions`
- `learningSessions`
- `codeDiagnostics`
- `hintInteractions` later
- `learningEvents` later
- `conceptMastery` later
- `gameSessions`
- `collaborationSessions`
- `peerReviewSubmissions`
- `remediationTriggers`

---

## 8. What Code Coach Stores Right Now

The most important collection for your component is `codeDiagnostics`.

Each saved diagnostic should contain at least:

- `userId`
- `learningSessionId`
- `diagnosticId`
- `errorType`
- `conceptTag`
- `explanationKey`
- `line`
- `column`
- `severity`
- `confidence`
- `mlProbability`
- `locatorConfidence`
- `detectionEngine`
- `status`
- `codeContextHash`
- `createdAt`
- `resolvedAt`

### 8.1 Meaning of Important Fields

#### `userId`

The student who made the mistake.

#### `learningSessionId`

The specific coding session where the mistake happened.

#### `diagnosticId`

A stable identifier for that diagnostic.

#### `errorType`

Which error category was detected.

For now, one of:

- `OFF_BY_ONE_LOOP_BOUNDARY`
- `INCORRECT_CONDITIONAL_OPERATOR`
- `ARRAY_LENGTH_INDEX_MISUSE`

#### `conceptTag`

The programming concept behind the mistake.

Examples:

- `loop_boundaries`
- `conditional_logic`
- `array_indexing`

#### `explanationKey`

A key used to map the issue to explanation content and hint logic.

#### `confidence`

The final confidence score of the diagnostic.

#### `mlProbability`

The ML model's confidence that the error category exists.

#### `locatorConfidence`

The confidence that the AST locator found the correct location.

#### `status`

This shows the current state of the diagnostic.

Typical values:

- `active`
- `resolved`
- `repeated`
- `ignored`

#### `codeContextHash`

Instead of storing raw source code, the system stores a hash of the important code snippet.

This is better for privacy.

---

## 9. Other Important Collections in the Shared Design

## 9.1 `users`

Stores student identity.

Important fields:

- `userId`
- `studentNumber`
- `fullName`
- `email`
- `role`
- `passwordHash`
- `status`
- `createdAt`

## 9.2 `authSessions`

Stores login session information.

Important fields:

- `authSessionId`
- `userId`
- `clientName` or `clientType`
- `refreshTokenHash`
- `createdAt`
- `lastSeenAt`
- `expiresAt`
- `status`

## 9.3 `learningSessions`

Groups learning activity into one session.

Important fields:

- `learningSessionId`
- `userId`
- `sourceComponent`
- `taskId`
- `language`
- `status`
- `startedAt`
- `endedAt`
- `lastAnalysisAt`

## 9.4 `gameSessions`

Stores gamification records.

Important fields:

- `userId`
- `learningSessionId`
- `gameType`
- `difficultyLevel`
- `score`
- `errorCount`
- `attemptCount`
- `hintUsage`
- `timeTakenSeconds`
- `traceAccuracy`

## 9.5 `collaborationSessions`

Stores pair programming session data.

Important fields:

- `driverUserId`
- `navigatorUserId`
- `learningSessionId`
- `taskId`
- `startedAt`
- `endedAt`
- `participationBalanceScore`
- `communicationQualityScore`

## 9.6 `peerReviewSubmissions`

Stores peer review records.

Important fields:

- `collaborationSessionId`
- `reviewerUserId`
- `revieweeUserId`
- `linkedDiagnosticId`
- `rubricScore`
- `feedbackQualityScore`
- `submittedAt`

## 9.7 `remediationTriggers`

Stores struggle/intervention records for Study Guider.

Important fields:

- `userId`
- `learningSessionId`
- `triggerSource`
- `conceptTag`
- `reason`
- `struggleLevel`
- `status`
- `createdAt`

## 9.8 `conceptMastery`

Stores the latest mastery state for each student per concept.

Important fields:

- `userId`
- `conceptTag`
- `masteryScore`
- `struggleScore`
- `lastUpdatedAt`

## 9.9 `learningEvents`

Stores general cross-component events.

This is useful because not every component should write directly into every other component's collection.

Instead, components can emit events such as:

- `code_diagnostic_detected`
- `hint_shown`
- `diagnostic_resolved`
- `struggle_signal_created`
- `game_session_completed`
- `pair_session_started`
- `peer_review_submitted`
- `micro_lesson_triggered`
- `quiz_completed`
- `mastery_updated`

---

## 10. How Code Coach Helps the Other Components

This is the most important integration section.

Code Coach helps the other components by acting as the **main diagnostic signal source**.

It tells the rest of the system:

- what error happened
- which concept is weak
- how often it happened
- whether it got resolved
- how much help the student needed

---

## 11. Code Coach -> Adaptive Gamification Engine

### 11.1 Why the Gamification Engine needs Code Coach

The Gamification Engine needs to know:

- what concept the student is weak in
- what type of mistake is repeating
- what kind of game is most useful now

Code Coach provides exactly that.

### 11.2 Where Code Coach comes into this component

Code Coach comes into the Gamification Engine in these sections:

1. **Game selection**
2. **Difficulty selection**
3. **Personalized practice**
4. **Hint adaptation**
5. **Progressive re-training**

### 11.3 What data the Gamification Engine needs from Code Coach

The Gamification Engine mainly needs:

- `userId`
- `learningSessionId`
- `errorType`
- `conceptTag`
- `repeat count`
- `confidence`
- `hint usage`
- `resolved vs unresolved`
- recent diagnostic history

### 11.4 Example workflow

```text
Student writes Java code
-> Code Coach detects OFF_BY_ONE_LOOP_BOUNDARY
-> same concept repeats several times
-> Gamification Engine reads that weakness
-> assigns Bug Hunt or Code Trace activity about loop boundaries
-> student plays targeted game
-> game performance is saved
-> future game difficulty is adapted
```

### 11.5 Example mapping

- `OFF_BY_ONE_LOOP_BOUNDARY`
  -> loop practice game
  -> bug hunt with loop boundary bugs
  -> code trace around loop execution

- `ARRAY_LENGTH_INDEX_MISUSE`
  -> array indexing practice
  -> bug hunt about array bounds
  -> code trace with array access

- `INCORRECT_CONDITIONAL_OPERATOR`
  -> boolean logic game
  -> bug hunt for conditions
  -> trace or prediction game for condition evaluation

---

## 12. Code Coach -> Collaborative Pair Programming and Peer Review Studio

### 12.1 Why the Collaborative component needs Code Coach

Collaboration is not only about sharing a workspace.

It also needs to understand:

- what technical issue the pair is stuck on
- what concept needs discussion
- which mistakes should become review targets

Code Coach provides this technical context.

### 12.2 Where Code Coach comes into this component

Code Coach comes into this component in these sections:

1. **Real-time pair support prompts**
2. **Peer review targets**
3. **Guided reflection**
4. **Collaboration quality support**
5. **Discussion scaffolding**

### 12.3 How Code Coach comes from the IDE into the web application

This is an important architecture point.

**Code Coach runs in the IDE, but the Collaborative Studio is a web application.**

That does **not** mean the web application talks directly to VS Code.

Instead, the integration path is:

```text
VS Code IDE
-> Code Coach detects issue
-> Code Coach backend saves diagnostic in MongoDB
-> Collaborative web app reads the saved diagnostic through shared backend/API
-> web app uses that data for pair programming and peer review support
```

So the real connection is:

```text
IDE -> Backend/API -> MongoDB -> Web App
```

It is **not**:

```text
IDE -> Web App directly
```

This is the best design because:

- the architecture stays clean
- the web app does not depend on VS Code internals
- all components use the same trusted backend data
- all records stay linked to the same logged-in user

### 12.4 Step-by-step workflow from IDE to Collaborative Studio

#### Step 1: Student writes code in the IDE

The student uses VS Code with Code Coach enabled.

Code Coach analyzes the Java file and may detect one of the current target errors.

#### Step 2: Code Coach saves the diagnostic

The backend saves the result in MongoDB under the authenticated user and the learning session.

Important stored fields include:

- `userId`
- `learningSessionId`
- `diagnosticId`
- `errorType`
- `conceptTag`
- `line`
- `column`
- `status`
- `confidence`
- `createdAt`

#### Step 3: Student opens the Collaborative web application

The student logs into the web app using the same shared platform identity.

Because the backend and database are shared, the web app can now fetch:

- recent Code Coach diagnostics for that student
- unresolved diagnostics
- repeated concept struggles
- diagnostics related to the current task

#### Step 4: Collaborative Studio uses Code Coach data

The web app transforms those saved diagnostics into collaborative support features.

Examples:

- pair-programming prompts
- guided discussion prompts
- peer review targets
- reflection prompts

#### Step 5: Pair programming support is shown

If the pair is working on the same concept that Code Coach already detected as weak, the web app can show a pedagogical prompt.

Example:

```text
Discuss why array.length is the number of elements, not the last valid index.
```

#### Step 6: Peer review links to the same issue

Later, when peer review happens, the same Code Coach diagnostic can be used as a review anchor.

That means the reviewer is not reviewing blindly.

The reviewer can focus on:

- the exact error type
- the concept behind the issue
- whether the student explained the reasoning properly

#### Step 7: Collaboration outcomes are stored

The Collaborative component can then store its own records such as:

- pair session details
- participation balance
- communication quality
- peer review quality
- linked diagnostic references

This creates a complete learning trail across the IDE and web app.

### 12.5 What data the Collaborative component needs from Code Coach

It mainly needs:

- `diagnosticId`
- `errorType`
- `conceptTag`
- `line`
- `column`
- `message`
- `status`
- repeated diagnostic patterns

### 12.6 Example workflow

```text
Two students are pair programming
-> Code Coach detects ARRAY_LENGTH_INDEX_MISUSE
-> Collaborative Studio sees the diagnostic
-> system shows a prompt such as:
   "Discuss what the last valid index of an array should be."
-> pair continues reasoning
-> after the task, peer review links to the same diagnostic
-> review quality and collaboration quality are stored
```

### 12.7 Why this matters

Without Code Coach, the collaboration component knows students are working together, but it does not know:

- what concept they are struggling with
- what issue should be discussed
- what the review should focus on

Code Coach gives the collaboration layer technical meaning.

---

## 13. Code Coach -> Student Progress Tracker / Study Guider

### 13.1 Why Study Guider needs Code Coach

Study Guider is the deep intervention layer.

It needs to know:

- which concept is repeatedly failing
- whether the student is stuck
- whether hints were enough or not
- whether the student resolved the issue or kept failing

Code Coach is the main source of this information.

### 13.2 Where Code Coach comes into this component

Code Coach comes into Study Guider in these sections:

1. **Struggle detection**
2. **Micro-lesson triggering**
3. **Concept mastery updates**
4. **Quiz targeting**
5. **Long-term progress tracking**

### 13.3 What data Study Guider needs from Code Coach

It mainly needs:

- `userId`
- `learningSessionId`
- `errorType`
- `conceptTag`
- repeated diagnostic count
- `status`
- `resolvedAt`
- time to fix
- hint usage level
- recent diagnostic history

### 13.4 Example workflow

```text
Student repeatedly gets ARRAY_LENGTH_INDEX_MISUSE
-> Code Coach stores diagnostics
-> Student Progress Tracker sees 3 repeated failures in array_indexing
-> struggle level becomes high
-> remediation trigger is created
-> Study Guider opens a micro-lesson about arrays
-> student completes quiz
-> concept mastery is updated
```

### 13.5 Why this is important

Code Coach gives immediate support.
Study Guider gives deeper support.

So the relationship is:

```text
Code Coach = immediate diagnosis
Study Guider = deeper pedagogical intervention
```

---

## 14. Full End-to-End Workflows Across the Platform

This section shows the total workflows.

## 14.1 Workflow 1: Normal IDE Coding Support

```text
Student logs in
-> opens Java file
-> extension creates learning session
-> student writes code
-> Code Coach analyzes code
-> ML predicts target error
-> AST locates issue
-> hint is shown
-> diagnostic is saved in MongoDB
```

This is the base workflow.

## 14.2 Workflow 2: Code Coach to Gamification

```text
Student repeatedly makes loop boundary mistakes
-> Code Coach stores diagnostics
-> Gamification Engine reads recent weak concept
-> assigns loop-focused game
-> student plays game
-> game result is saved
-> student profile is updated
```

## 14.3 Workflow 3: Code Coach to Collaboration

```text
Students pair program on a Java task
-> Code Coach detects a target error
-> Collaborative Studio links that issue to the pair session
-> system provides a pedagogical prompt
-> students discuss and fix
-> peer review later references the same issue
-> collaboration and review data are stored
```

## 14.4 Workflow 4: Code Coach to Study Guider

```text
Student keeps making the same concept mistake
-> Code Coach saves repeated diagnostics
-> Progress Tracker detects struggle pattern
-> remediation trigger is created
-> Study Guider generates micro-lesson
-> student reads lesson
-> student completes quiz
-> concept mastery is updated
```

## 14.5 Workflow 5: Full Closed Learning Loop

```text
Code Coach detects problem
-> Gamification gives practice
-> Collaboration gives guided discussion
-> Study Guider gives deep remediation
-> quiz validates learning
-> mastery profile updates
-> future support becomes more personalized
```

This is the ideal full Code Guru vision.

---

## 15. What Data Each Component Needs

The table below gives a simplified integration view.

| Component | Needs from Code Coach | Why it needs it |
|---|---|---|
| Adaptive Gamification Engine | `errorType`, `conceptTag`, repeat count, hint usage, resolved/unresolved | to choose game type, difficulty, and practice area |
| Collaborative Studio | `diagnosticId`, `errorType`, `conceptTag`, location, status | to generate pair prompts and link peer review to technical issues |
| Student Progress Tracker / Study Guider | `errorType`, `conceptTag`, repeat count, time-to-fix, hint dependency, resolution history | to detect struggle, trigger micro-lessons, update mastery |
| Dashboard / Analytics layer later | diagnostic history, concept struggle, session trends | to show progress and lecturer insights |

---

## 16. Where Code Coach Comes Into Other Components

This section answers your question very directly.

### 16.1 In the Gamification component, Code Coach comes in at:

- weakness detection
- targeted game recommendation
- difficulty adaptation input
- post-game re-evaluation

### 16.2 In the Collaborative component, Code Coach comes in at:

- live pair programming guidance
- collaboration prompt generation
- peer review linking
- review focus suggestion

### 16.3 In the Study Guider component, Code Coach comes in at:

- struggle pattern detection
- remediation trigger logic
- concept mastery update input
- quiz topic selection

So in short:

```text
Gamification uses Code Coach for practice targeting.
Collaboration uses Code Coach for guided discussion and review context.
Study Guider uses Code Coach for intervention and remediation.
```

---

## 17. Current Technical Architecture of Code Coach

Right now, Code Coach is an **ML-led hybrid system**.

That means:

- ML is used more than rules for error-type detection
- AST rules are still used for exact localization

### 17.1 Current pipeline

```text
Java code
-> Tree-sitter AST parsing
-> feature extraction
-> ML classifiers predict the 3 target error types
-> only ML-positive categories are passed to AST locators
-> locator finds line/column and context
-> hint engine produces beginner-friendly hints
-> results are stored and shown in the extension
```

### 17.2 Why this design is good for now

It is a good research design because:

- ML is genuinely involved in decision-making
- localization is still reliable
- the output is explainable
- the system is easier to defend academically than pretending pure ML localizes spans directly

---

## 18. Current Backend/API Picture

The important live backend areas now are:

- authentication
- learning sessions
- Code Coach analysis
- Mongo persistence

Important route groups:

- `/api/v1/auth`
- `/api/v1/learning-sessions`
- `/api/v1/code-coach/analyze`

### 18.1 Auth workflow

```text
register/login
-> backend returns JWT
-> extension stores tokens
-> later requests include Authorization header
```

### 18.2 Session workflow

```text
extension creates or resumes learning session
-> session belongs to authenticated user
-> analysis must use that session
```

### 18.3 Analysis workflow

```text
authenticated request
-> backend verifies token
-> backend checks session ownership
-> Code Coach analyzes code
-> diagnostics saved in MongoDB
-> response returned to extension
```

---

## 19. Example Data Flow Through the Whole System

Here is one realistic example.

### Scenario: Student misuses `array.length`

1. Student logs in through VS Code
2. Extension creates learning session
3. Student writes:

```java
System.out.println(arr[arr.length]);
```

4. Code Coach detects `ARRAY_LENGTH_INDEX_MISUSE`
5. Diagnostic is shown
6. Diagnostic is saved:
   - under that user
   - under that session
   - with `conceptTag = array_indexing`
7. If repeated:
   - Gamification Engine may assign array indexing game
   - Collaborative Studio may prompt pair discussion
   - Study Guider may trigger array micro-lesson
8. Quiz later checks whether the student now understands valid array indices
9. Concept mastery for `array_indexing` is updated

This is the full educational loop.

---

## 20. Recommended Integration Strategy for the Team

If your team wants to implement the project safely, the best integration order is:

1. shared authentication
2. shared learning sessions
3. Code Coach diagnostic persistence
4. shared event contracts
5. Gamification integration
6. Collaboration integration
7. Study Guider integration
8. mastery and dashboard layer

### Why this order is good

Because all later components depend on:

- user identity
- session identity
- stored diagnostic signals

Without those, the other components would have no reliable source of truth.

---

## 21. Simple Team Responsibilities

A clean team split could look like this:

### Code Coach team

- error detection
- localization
- hinting
- diagnostic persistence
- hint interaction logging

### Gamification team

- game modules
- adaptive rule engine
- game session logging
- weak concept based game routing

### Collaborative team

- pair session management
- peer review workflow
- collaboration metrics
- prompt generation

### Study Guider team

- struggle detection
- remediation triggers
- micro-lessons
- quizzes
- concept mastery updates

### Shared platform work

- authentication
- session model
- integration contracts
- shared database collections

---

## 22. What Is Already Working in Your Current System

From the current implementation, these things are already real:

- Code Coach detects the 3 target error types
- the backend is ML-led for those 3 errors
- the VS Code extension shows diagnostics and hints
- login UI works
- JWT auth works
- learning sessions work
- diagnostics are saved in MongoDB
- the full extension flow has already been tested end to end

That means you already have the **foundation** of the bigger Code Guru system.

---

## 23. What Still Needs to Be Implemented Later

The bigger platform still needs:

- shared `learningEvents`
- repeated diagnostic analytics
- hint interaction persistence
- gamification event ingestion
- collaboration event ingestion
- remediation trigger engine
- micro-lesson and quiz flow
- concept mastery updates
- dashboards

So the current system is a strong beginning, but not yet the complete Code Guru platform.

---

## 24. Final Big Picture Summary

If you want one short summary of the whole project, this is it:

**Code Guru** is a beginner programming learning ecosystem.

- **Code Coach** gives immediate coding help and produces diagnostic signals.
- **Adaptive Gamification Engine** gives targeted game-based practice based on those signals.
- **Collaborative Pair Programming and Peer Review Studio** improves collaborative learning using those signals and collaboration analytics.
- **Student Progress Tracker / Study Guider** detects repeated struggle and gives deeper remediation through micro-lessons and quizzes.

Code Coach is the main signal provider because it is the first component that understands:

- what mistake happened
- what concept is weak
- where the issue is
- how often it repeats

That is why storing Code Coach diagnostics under the correct logged-in user in MongoDB is essential.

Without that stored user-linked diagnostic data, the other components cannot personalize learning correctly.

---

## 25. Suggested PDF Structure

If you want to turn this into a PDF report, use this section order:

1. Introduction to Code Guru
2. Educational problem being solved
3. Overview of the four components
4. Why Code Coach is the mainstream component
5. Current Code Coach error types
6. Code Coach A to Z workflow
7. Database design and stored data
8. Integration with Gamification
9. Integration with Collaborative Studio
10. Integration with Study Guider
11. Full system workflows
12. Current implementation status
13. Future implementation roadmap

---

## 26. Related Project Docs

- [Code Guru Shared Data Model](C:/Hello/Tutorials/code-coach/docs/code_guru_shared_data_model.md)
- [Code Guru Integration API Contract](C:/Hello/Tutorials/code-coach/docs/code_guru_integration_api_contract.md)
- [Code Guru Phase 1 Implementation Plan](C:/Hello/Tutorials/code-coach/docs/code_guru_phase1_implementation_plan.md)
- [Code Coach Proposal Traceability](C:/Hello/Tutorials/code-coach/docs/proposal_traceability.md)
