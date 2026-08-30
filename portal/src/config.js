/**
 * Every environment value the portal reads, in one place.
 *
 * codeguru-auth.js and handoff.js deliberately take their configuration as
 * arguments so they can stay identical across three repos with three different
 * bundlers. This module is the Vite-specific half that feeds them.
 */

export const CODE_COACH_URL =
  import.meta.env.VITE_CODE_COACH_URL || 'http://127.0.0.1:8000';

export const ALLOWED_REDIRECTS = import.meta.env.VITE_ALLOWED_REDIRECTS || '';

export const STUDY_GUIDER_URL = import.meta.env.VITE_STUDY_GUIDER_URL || '';
export const PAIRPATH_URL = import.meta.env.VITE_PAIRPATH_URL || '';
export const GAMIFICATION_URL = import.meta.env.VITE_GAMIFICATION_URL || '';

export const DEV_LOGIN_FLAG = import.meta.env.VITE_ENABLE_DEV_LOGIN;

/**
 * Identifies this client to Code Coach. It is stored on the auth session, so a
 * student can see which app a session belongs to — the VS Code extension uses
 * "code-coach-vscode", PairPath uses "pair-review-studio".
 */
export const CLIENT_NAME = 'codeguru-portal';

/**
 * The fixed loopback port the VS Code extension listens on during browser
 * sign-in.
 *
 * Fixed rather than ephemeral because redirect_uri is validated by exact
 * origin: a random port could never be on the allow-list. It has to appear in
 * VITE_ALLOWED_REDIRECTS as http://127.0.0.1:53682 for the flow to work, which
 * means the allow-list is not loosened to make room for it.
 */
export const VSCODE_LOOPBACK_PORT = import.meta.env.VITE_VSCODE_LOOPBACK_PORT || '53682';
