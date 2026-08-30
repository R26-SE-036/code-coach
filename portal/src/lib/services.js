/**
 * The platform's service registry, and the one way to open a service with the
 * student's session attached.
 *
 * The portal is the only app that knows where the other three live. Siblings
 * link to {portal}/go?to=<key> and let this module resolve the key, which is
 * why adding or moving a service is a change in one repo rather than four.
 */
import { loadTokens } from './codeguru-auth.js';
import { buildHandoffUrl, isAllowedRedirect, parseAllowedOrigins } from './handoff.js';
import {
  ALLOWED_REDIRECTS,
  GAMIFICATION_URL,
  PAIRPATH_URL,
  STUDY_GUIDER_URL,
} from '../config.js';

/**
 * `key` is the value CodeGuruBar puts in /go?to=. `countKey` names the field in
 * Code Coach's dashboard overview `counts` that this service contributes to,
 * so the Home page can show a live number per card.
 */
export const SERVICES = [
  {
    key: 'study-guider',
    name: 'Study Guider',
    url: STUDY_GUIDER_URL,
    description: 'Micro-lessons and quizzes for the concepts you keep getting stuck on.',
    countKey: 'active_remediation_triggers',
    countLabel: 'open remediations',
  },
  {
    key: 'pairpath',
    name: 'PairPath',
    url: PAIRPATH_URL,
    description: 'Pair programming sessions with live coaching and peer review.',
    countKey: 'total_pair_sessions',
    countLabel: 'pair sessions',
  },
  {
    key: 'gamification',
    name: 'Games',
    url: GAMIFICATION_URL,
    description: 'Adaptive practice games pitched at the concepts you find hardest.',
    countKey: 'total_game_sessions',
    countLabel: 'games played',
  },
];

export function serviceByKey(key) {
  return SERVICES.find((service) => service.key === key) || null;
}

/** Services that actually have a URL configured. One without is not offered. */
export function configuredServices() {
  return SERVICES.filter((service) => service.url);
}

/**
 * Send the browser to `serviceUrl` carrying the current session.
 *
 * Returns an error string instead of navigating when the destination is not on
 * the allow-list. That is configuration rather than user input, but a typo in
 * VITE_PAIRPATH_URL should fail visibly here rather than quietly post an access
 * token to whatever that typo resolves to.
 */
export function handOffTo(serviceUrl, user) {
  if (!serviceUrl) {
    return 'That service has no URL configured in the portal environment.';
  }

  const allowed = parseAllowedOrigins(ALLOWED_REDIRECTS);
  if (!isAllowedRedirect(serviceUrl, allowed)) {
    return (
      serviceUrl + ' is not in VITE_ALLOWED_REDIRECTS, so the portal will not send your token there.'
    );
  }

  const { accessToken, refreshToken, expiresAt } = loadTokens();
  const expiresIn = expiresAt ? Math.max(0, Math.round((expiresAt - Date.now()) / 1000)) : '';

  window.location.href = buildHandoffUrl(serviceUrl, {
    tokens: {
      access_token: accessToken,
      refresh_token: refreshToken,
      expires_in: expiresIn,
    },
    user,
  });

  return '';
}
