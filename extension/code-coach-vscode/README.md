# Code Coach for VS Code

Code Coach helps you learn Java by explaining the mistakes in your code, not only
pointing at them. As you type, it looks for the errors beginners make most often
and walks you towards a fix with **three levels of hints**. It starts with the
idea behind the mistake and ends with a specific suggestion, so you can stop as
soon as you understand.

Code Coach is one component of **Code Guru**, a learning platform for novice
Java programmers (research project R26-SE-036). You use one account across the
extension and the Code Guru web portal. The mistakes you work through in VS Code
feed the portal's study plan, practice games and pair programming.

---

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installing](#installing)
- [Getting started](#getting-started)
- [Commands](#commands)
- [Settings](#settings)
- [What is sent, and where](#what-is-sent-and-where)
- [Troubleshooting](#troubleshooting)
- [For developers](#for-developers)
- [Releasing a new version](#releasing-a-new-version)

---

## Features

**Analysis as you type.** Open a `.java` file and Code Coach checks it when you
pause typing for about a second. It also re-checks when you switch files. To
check straight away, run **Code Coach: Analyze Current File**, or click Code
Coach's item in the status bar.

**Findings where you are working.** Each finding is underlined in the editor and
listed in the **Problems** panel with the source *Code Coach*. A **CodeLens**
link sits above each line that has a finding.

**Progressive hints.** Every finding comes with three hints, revealed one at a
time:

| Level | What it gives you |
|---|---|
| 💡 **Concept** | The idea behind the mistake, such as how array indexes start at 0 |
| 🧭 **Guidance** | Where to look, and what question to ask yourself |
| 🎯 **Targeted** | A specific suggestion for this line |

Open them from the 💡 lightbulb on an underline, from the CodeLens link, or with
**Code Coach: Next Hint** and **Code Coach: Previous Hint**.

**The Coach Panel.** Click the Code Coach icon in the Activity Bar, or the Code
Coach icon in the title bar of any Java editor. The panel lets you:
- step through the file's findings one at a time;
- see each finding's hints side by side;
- follow the current session.

**Report a false positive.** If a finding is wrong, report it from the lightbulb
menu or the Coach Panel. These reports are used to measure and improve the
detector.

**Browser sign-in.** Signing in opens the Code Guru portal in your browser. After
you sign in there, VS Code is signed in automatically. You never type a password
into the editor.

**A welcome guide.** **Code Coach: Welcome Guide** is a five-step walkthrough:
sign in, open a Java file, analyse it, explore the hints, and use the panel.

**Status bar.** Code Coach has two status bar items:
- **What it is doing:** *Ready*, *Analyzing*, or *Sign In for Code Coach*.
  Clicking it analyses the current file, or signs you in if needed.
- **Who you are signed in as.** Clicking your name signs you out.

## Requirements

- **VS Code 1.110** or newer.
- **An internet connection.** Analysis runs on the Code Guru server, not on your
  machine, so you do **not** need a JDK installed for Code Coach itself.
- **A Code Guru account.** You can create one from the extension; see
  [Getting started](#getting-started).

## Installing

Code Coach is distributed as a `.vsix` file on the project's GitHub Releases
page.

1. Open **<https://github.com/R26-SE-036/code-coach/releases>** and find the newest
   release named **Code Coach extension vX.Y.Z**.
2. Under **Assets**, download `code-coach-X.Y.Z.vsix`.
3. Install it in VS Code in one of two ways:
   - **From the Extensions view:** press `Ctrl+Shift+X` (`Cmd+Shift+X` on macOS),
     open the **⋯** menu at the top of the view, choose **Install from VSIX…**,
     and pick the file.
   - **From a terminal:**

     ```bash
     code --install-extension code-coach-X.Y.Z.vsix
     ```

4. Reload VS Code if it asks you to.

**Updating:** install the newer `.vsix` the same way, and it replaces the old
version. **Uninstalling:** open the Extensions view, find *Code Coach*, and choose
**Uninstall**.

## Getting started

1. **Open Code Coach.** Click its icon in the Activity Bar, or run
   **Code Coach: Welcome Guide** from the Command Palette (`Ctrl+Shift+P`).
2. **Sign in.** Choose **Sign In** from the panel, the walkthrough, or the status
   bar. Your browser opens the Code Guru sign-in page. Sign in, or choose
   **Create Account** to register, and then return to VS Code. The status bar now
   shows your name.
3. **Open a `.java` file** and start typing. Findings appear shortly after you
   pause.
4. **Work through the hints** from the lightbulb, the CodeLens link or the Coach
   Panel. Reveal as few as you need.

Your sign-in lasts across restarts. **Code Coach: Sign Out** ends it.

<details>
<summary>How browser sign-in works, and what happens if it cannot</summary>

- **The normal route.** The extension briefly listens on
  `http://127.0.0.1:53682` on your own machine. After you sign in, the portal
  sends the browser back to that address with a **single-use code** that is
  valid for two minutes. The extension exchanges the code for its own session,
  so no password or token ever appears in a URL.
- **Fallbacks.** If the browser cannot reach that address, the portal can hand
  the session back through a `vscode://` link instead. If that fails too, Code
  Coach asks for your email and password in VS Code.
- **Remote windows.** In SSH, WSL, dev containers and Codespaces, the loopback
  address is not your machine, so Code Coach uses those VS Code prompts directly.
- **Timeout.** A browser sign-in that has not finished after three minutes is
  cancelled, and you can start again.

</details>

## Commands

Open the Command Palette (`Ctrl+Shift+P`, or `Cmd+Shift+P` on macOS) and type
*Code Coach*.

| Command | What it does |
|---|---|
| Code Coach: Start | Offers the next step: sign in, analyse the current file, or open the panel |
| Code Coach: Sign In | Signs in through the Code Guru portal in your browser |
| Code Coach: Create Account | Opens the portal's registration page |
| Code Coach: Sign Out | Ends your session in VS Code |
| Code Coach: Analyze Current File | Checks the active Java file now |
| Code Coach: Open Coach Panel | Opens the panel for the active file |
| Code Coach: Next Hint / Previous Hint | Moves between hint levels for the current finding |
| Code Coach: Report False Positive | Tells the team a finding was wrong |
| Code Coach: Welcome Guide | Opens the five-step walkthrough |

## Settings

Open **Settings** (`Ctrl+,`) and search for *Code Coach*. Most students never
need to change anything.

| Setting | Default | Purpose |
|---|---|---|
| `codeCoach.portalUrl` | `https://13-202-201-115.sslip.io` | The Code Guru web portal, where Sign In and Create Account open |
| `codeCoach.backendUrl` | `https://13-202-201-115.sslip.io` | Where the extension sends code for analysis |
| `codeCoach.enableEvaluationLogging` | `false` | Also records anonymised diagnostic events for the research evaluation |

`portalUrl` and `backendUrl` should point at the **same** platform. If they
don't, you sign in to one server and send your code to another.

## What is sent, and where

Everything goes to the Code Guru server set in the two URL settings, over
HTTPS.

- **Your code.** When the active Java file is analysed, its contents are sent
  with the ID of your current learning session. Nothing else from your workspace
  is sent, and other files and folders are never read.
- **Learning events.** When you are signed in, the extension records hint
  activity to your account: showing a hint, moving between hint levels, and
  reporting a false positive. The platform uses these events to judge which
  concepts you are struggling with, and they shape your study plan in the
  portal.
- **Evaluation logging.** This is off unless you turn on
  `codeCoach.enableEvaluationLogging`. It adds anonymised diagnostic records
  used to evaluate the detector for the research project.
- **Your session.** Access and refresh tokens are kept in VS Code's secret
  storage, which uses your operating system's keychain. Your display name is
  cached so the status bar can show it. **Sign Out** deletes all of it.

## Troubleshooting

**The status bar keeps saying "Sign In for Code Coach".**
You are not signed in, or your session has expired. Run
**Code Coach: Sign In**.

**The browser opened, I signed in, and VS Code did not notice.**
- Make sure you signed in within three minutes, then try again.
- Security software sometimes blocks the local address `127.0.0.1:53682`. If it
  keeps failing, cancel the browser sign-in and use the email and password
  prompts VS Code offers instead.

**"Port 53682 is already in use".**
Another VS Code window is part-way through signing in. Finish or cancel it
there, or close that window, and try again.

**No findings appear.**
- Code Coach analyses Java files only, meaning files VS Code shows as *Java* in
  the bottom-right corner.
- Check that you are signed in and online.
- Open **View → Output** and choose **Code Coach** from the list. The log shows
  each request and anything that went wrong.

**I am using a local copy of the platform.**
Set both URL settings to your own server; see
[Pointing at a local stack](#pointing-at-a-local-stack).

## For developers

The extension is plain TypeScript with no runtime dependencies. The source is in
`src/`:

| File | Responsibility |
|---|---|
| `extension.ts` | Activation, commands, and editor event wiring |
| `analysis.ts` | Sends code for analysis and turns results into diagnostics and hints |
| `auth.ts`, `browserAuth.ts` | Sign-in (browser and prompts), sessions, learning events |
| `api.ts` | HTTP calls, token refresh, and settings |
| `ui/` | The Coach Panel, CodeLens, code actions, decorations, and status bar |

### Build and run

```bash
npm ci
npm run compile
```

Then press **F5** in VS Code to open an Extension Development Host with the
extension loaded. `npm run watch` recompiles on every save.

### Pointing at a local stack

With the Code Guru compose stack running (`codeguru-web/deploy`), add this to your
user or workspace `settings.json`:

```json
{
  "codeCoach.portalUrl": "http://localhost:8090",
  "codeCoach.backendUrl": "http://localhost:8090"
}
```

### Tests

```bash
npm test
```

This compiles, lints, and runs the suite inside a downloaded copy of VS Code.

- **Settings and browser sign-in tests** need nothing running. They start their
  own fake server.
- **Live platform tests** create a test account, sign in, and analyse a real
  file against the server at `CODE_COACH_TEST_URL`. The default is the local
  stack at `http://localhost:8090`, and the tests skip themselves if nothing
  answers there.
- **To run the live tests against the deployed platform:**

  ```bash
  CODE_COACH_TEST_URL=https://13-202-201-115.sslip.io npm test
  ```

  These create clearly named `example.com` accounts on that server.

### Packaging locally

```bash
npx @vscode/vsce package --no-dependencies
```

This produces `code-coach-vscode-<version>.vsix`, which you can install with
`code --install-extension`.

## Releasing a new version

Releases are automated by the `Extension release` workflow in this repository
(`.github/workflows/extension-release.yml`):

1. **Raise `version`** in `package.json` and add an entry to `CHANGELOG.md`.
2. **Merge to `main`** as usual.
3. **The workflow runs:**
   - it runs the tests, including the live suite against the deployed platform;
   - it packages the extension;
   - if no release exists for that version yet, it publishes one tagged
     `extension-vX.Y.Z`, with the `.vsix` attached.

A merge that leaves the version unchanged runs the tests and packaging but
publishes nothing, so ordinary changes never overwrite a release people have
installed.
