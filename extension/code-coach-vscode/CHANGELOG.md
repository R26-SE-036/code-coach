# Change Log

All notable changes to the Code Coach extension are recorded here. Each version
listed is published as a GitHub Release tagged `extension-v<version>`, with its
`.vsix` attached.

## [Unreleased]

- **Released under the MIT License.** The `.vsix` now includes the licence
  text.

## [0.1.0] - 2026-09-21

The first release installable outside a development host.

- **Connects to the deployed Code Guru platform by default.** The portal and the
  backend both point at `https://13-202-201-115.sslip.io`. They used to point at
  a local stack at `http://localhost:8090`, which an installed copy has no way
  to reach.
- **Analysis as you type**, and on demand, for Java files.
- **Three-level progressive hints** for each finding (Concept, Guidance,
  Targeted), shown through the lightbulb, CodeLens and the Coach Panel.
- **The Coach Panel**, for moving between findings and their hints.
- **Browser sign-in through the Code Guru portal**, using a single-use code. It
  falls back to a `vscode://` link, and then to prompts in VS Code.
- **False-positive reporting** from the lightbulb menu and the Coach Panel.
- **A five-step welcome walkthrough.**
