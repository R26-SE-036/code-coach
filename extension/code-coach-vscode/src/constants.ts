export const ACCESS_TOKEN_SECRET = "codeCoach.accessToken";
export const REFRESH_TOKEN_SECRET = "codeCoach.refreshToken";
export const USER_STATE_KEY = "codeCoach.user";
export const LEARNING_SESSION_KEY = "codeCoach.learningSessionId";
export const CLIENT_NAME = "code-coach-vscode";
export const DEBOUNCE_DELAY_MS = 900;

/**
 * Where the platform is, unless the student's settings say otherwise: the
 * deployed edge (Caddy on the AWS host), which serves both the web app and
 * Code Coach's /api/v1 from one origin.
 *
 * It used to be the compose stack's http://localhost:8090, which suited running
 * the extension with F5 and nothing else: an installed copy, on a student's own
 * machine with no stack running, would open a sign-in page nothing served. A
 * developer running the stack sets both settings to http://localhost:8090.
 *
 * Both settings once defaulted to dev-server ports instead - the portal to 4200,
 * the backend to 8000 - so sign-in opened one server and redeemed its code at
 * another. One address for both is the point. Must match package.json.
 */
export const DEFAULT_PLATFORM_URL = "https://13-202-201-115.sslip.io";

/** The compose stack's edge, for developers and for the test suite's default. */
export const LOCAL_STACK_URL = "http://localhost:8090";
