# Change Log

All notable changes to the Code Coach extension are recorded here. Each version
listed is published as a GitHub Release tagged `extension-v<version>`, with its
`.vsix` attached.

## [Unreleased]

## [0.2.0] - 2026-09-24

- **Released under the MIT License.** The `.vsix` now includes the licence
  text.
- **Email and password when browser sign-in cannot finish.** A cancelled or
  timed-out browser sign-in now offers the prompts, so a student whose security
  software blocks `127.0.0.1:53682` can still sign in.
- **The `vscode://` sign-in handler is removed.** The portal never produced that
  link, so the fallback 0.1.0 described did not exist, and the handler would
  redeem a code from any `vscode://` link.
- **The hover card shows one hint level at a time**, with a link to the next,
  like the lightbulb and the Coach Panel. It used to show all three at once.
- **Analyze Current File is listed once** in the command contributions.
- **The Code Guru logo.** The extension now uses the website's mark - in the
  Extensions view, the activity bar and the editor toolbar - instead of its own
  graduation cap. The light-theme toolbar icon was white, and so invisible.
- **"Forgot password?"** after a wrong password in the sign-in prompts opens
  the website's reset page.

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
