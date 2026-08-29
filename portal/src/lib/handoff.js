/**
 * The portal side of the token handoff.
 *
 * A sibling frontend with no session sends the student here as
 *   {portal}/login?redirect_uri={their_url}
 * and after a successful sign-in we send them back with the tokens in the URL
 * fragment.
 *
 * The allow-list below is the whole security of this design. Without it the
 * portal is an open redirect: anyone could link a student to
 * /login?redirect_uri=https://attacker.example, and the moment that student
 * signed in we would hand their platform access token straight to the
 * attacker. Every change in this file should be read with that in mind.
 */

/**
 * Parse VITE_ALLOWED_REDIRECTS — a comma-separated list of allowed origins,
 * e.g. "http://localhost:5173,http://localhost:3000".
 */
export function parseAllowedOrigins(raw) {
  return String(raw || '')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => {
      try {
        return new URL(entry).origin;
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

/**
 * Is this redirect target one of ours?
 *
 * Compares the parsed **origin** only — never a string prefix. A prefix check
 * such as candidate.startsWith(allowed) would accept
 * "http://localhost:5173.attacker.example", which is a different host
 * entirely. Comparing origins after URL parsing is what makes that
 * impossible.
 */
export function isAllowedRedirect(candidate, allowedOrigins) {
  if (!candidate) return false;

  let url;
  try {
    url = new URL(candidate);
  } catch {
    return false;
  }

  // Only real web schemes. Blocks javascript: and data: targets.
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return false;

  return allowedOrigins.includes(url.origin);
}

/**
 * Build the URL to send the student back to, with the session in the fragment.
 *
 * Fragment, not query string: fragments are not transmitted to servers, so the
 * token stays out of the target's access logs and out of any Referer header it
 * later sends. The receiving app calls consumeHandoffFragment() from
 * codeguru-auth, which stores the tokens and immediately scrubs the URL.
 */
export function buildHandoffUrl(redirectUri, authResponse) {
  const { tokens, user } = authResponse;

  const fragment = new URLSearchParams({
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token || '',
    expires_in: String(tokens.expires_in || ''),
    user_id: user?.user_id || '',
  });

  // Drop anything the target app already had in its own fragment.
  return redirectUri.split('#')[0] + '#' + fragment.toString();
}

/**
 * Resolve the redirect_uri for the current page load.
 *
 * Returns { redirectUri, rejected }. `rejected` is true when the caller asked
 * for a target we do not allow — the UI shows that as an error rather than
 * silently falling back to the hub, because a rejected redirect usually means
 * either a misconfigured teammate service or an attempt to steal a token, and
 * both deserve to be visible.
 */
export function resolveRedirectUri(search, allowedOriginsRaw) {
  const requested = new URLSearchParams(search).get('redirect_uri');
  if (!requested) return { redirectUri: null, rejected: false };

  const allowed = parseAllowedOrigins(allowedOriginsRaw);
  if (!isAllowedRedirect(requested, allowed)) {
    return { redirectUri: null, rejected: true, requested };
  }

  return { redirectUri: requested, rejected: false };
}
