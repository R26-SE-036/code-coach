export const ACCESS_TOKEN_SECRET = "codeCoach.accessToken";
export const REFRESH_TOKEN_SECRET = "codeCoach.refreshToken";
export const USER_STATE_KEY = "codeCoach.user";
export const LEARNING_SESSION_KEY = "codeCoach.learningSessionId";
export const CLIENT_NAME = "code-coach-vscode";
export const DEBOUNCE_DELAY_MS = 900;

/**
 * Where the platform is, unless the student's settings say otherwise: the
 * compose stack's edge (Caddy, HTTP_PORT=8090), which serves both the web app
 * and Code Coach's /api/v1. Both settings used to default to dev-server ports -
 * the portal to 4200, the backend to 8000 - so against the stack, sign-in opened
 * a page nothing was serving and then redeemed its code at a port nothing was
 * listening on. Must match the defaults in package.json.
 */
export const DEFAULT_PLATFORM_URL = "http://localhost:8090";
