# Code Coach

Code Coach finds beginner logic mistakes in Java while the student types, and
explains them with hints that start general and get more specific only when
asked. It is a VS Code extension backed by a FastAPI service, and it is also
the Code Guru platform's identity provider: every other component signs
students in through it.

It catches **30 error types** - mistakes that compile and run but give the
wrong answer, such as a loop that stops one element early, `==` on strings, an
accumulator reset inside its loop, or a `switch` case without `break`. The
full list, with each type's concept tag and hints, is
[`knowledge_base/code_coach_errors.json`](knowledge_base/code_coach_errors.json).

## How a mistake is found

```text
Java source
  -> Tree-sitter parse (the code does not have to compile)
  -> candidate sites: each loop, comparison, condition, assignment ... that
     could hold one of the error types
  -> a model per error type scores each candidate site
     (a few older types use a file-level classifier gate, or an AST rule)
  -> locator: exact line and column, and the code it quotes
  -> hint engine: concept -> guidance -> targeted hint about THIS code
```

The program is never executed. Diagnostics carry the error type, line, a
confidence, the concept tag shared with the rest of Code Guru, and a stable
`diagnostic_id` so a student can report a false positive once and not see it
again.

## Repository layout

| Path | What it is |
|---|---|
| `extension/code-coach-vscode/` | The VS Code extension (TypeScript). Its own [README](extension/code-coach-vscode/README.md) and [CHANGELOG](extension/code-coach-vscode/CHANGELOG.md). |
| `backend/` | The FastAPI service: analysis, accounts, learning signals, billing. See [backend/README.md](backend/README.md). |
| `knowledge_base/` | Error catalogue, hint templates, lessons, game catalogue and worked examples shared with the other components. |
| `data/ml/` | Labelled Java snippets, extracted features and dataset splits. |
| `integration/` | The cross-component API contract ([API_CONTRACT.md](integration/API_CONTRACT.md), `openapi.json`) and the platform setup guide. |
| `Dockerfile` | The production image of the backend. |

## Running it

The backend needs a MongoDB Atlas connection string and a JWT secret in
`backend/.env` (see [backend/README.md](backend/README.md)).

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload    # http://127.0.0.1:8000
```

The extension:

```bash
cd extension/code-coach-vscode
npm install
npm run compile
```

Open that folder in VS Code and press `F5`. Point the `codeCoach.backendUrl`
setting at `http://127.0.0.1:8000` to use the local backend; the default is the
live server. Students install the published extension from the Marketplace or
from a `.vsix` on the GitHub release instead.

The whole platform can also run as one Docker Compose stack from
`codeguru-web/deploy` - see that repository.

## Tests

```bash
cd backend && .venv/Scripts/python -m pytest
cd extension/code-coach-vscode && npm test
```

## Releases and deployment

- **Backend:** a push to `main` runs the tests, builds the image, pushes it to
  ECR and deploys it to the AWS server (`.github/workflows/deploy.yml`).
- **Extension:** a push to `main` with a new `version` in its `package.json`
  publishes a GitHub release `extension-v<version>` with the `.vsix`, using the
  matching CHANGELOG section as the notes (`.github/workflows/extension-release.yml`).
  It is published to the Marketplace as well when the `VSCE_PAT` secret is set.

## Evaluation tools

Everything used to build, train and measure the models is in
`backend/app/dev_tools/`: dataset builders, training and threshold calibration,
the mutation-based comparison against CodeBERT, model cards, and the
per-source evaluation. Some of them connect to the live database
(`dispute_report.py`, `derive_concept_prerequisites.py`,
`export_code_snapshots.py`), and `seed_student.py` creates an account through
a running API, so read a script before running it.
