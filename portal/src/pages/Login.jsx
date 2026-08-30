import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import AuthShell from '../components/AuthShell.jsx';
import { createHandoffCode, login, saveTokens } from '../lib/codeguru-auth.js';
import {
  buildCodeHandoffUrl,
  buildHandoffUrl,
  isVsCodeLoopback,
  resolveRedirectUri,
} from '../lib/handoff.js';
import {
  ALLOWED_REDIRECTS,
  CLIENT_NAME,
  CODE_COACH_URL,
  VSCODE_LOOPBACK_PORT,
} from '../config.js';

/**
 * The platform's canonical sign-in form.
 *
 * The field is called "identifier", not "email", because that is what Code
 * Coach's login endpoint accepts — and it accepts a username too, so the
 * input is type="text". Using type="email" would make the browser block a
 * valid username before the form was ever submitted.
 */
export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const { redirectUri, rejected, requested } = resolveRedirectUri(
    location.search,
    ALLOWED_REDIRECTS,
  );

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);

    try {
      const auth = await login(CODE_COACH_URL, {
        identifier: identifier.trim(),
        password,
        clientName: CLIENT_NAME,
      });

      saveTokens(auth);

      // The VS Code extension listens on a loopback HTTP server, which never
      // sees a URL fragment. It gets a single-use code in the query string
      // instead, and redeems it for a session of its own.
      if (redirectUri && isVsCodeLoopback(redirectUri, VSCODE_LOOPBACK_PORT)) {
        const code = await createHandoffCode(
          CODE_COACH_URL,
          auth.tokens.access_token,
          'code-coach-vscode',
        );
        window.location.href = buildCodeHandoffUrl(redirectUri, code);
        return;
      }

      if (redirectUri) {
        // Hand the session back to the service that sent the student here.
        // Full page navigation, not the router: the target is another origin.
        window.location.href = buildHandoffUrl(redirectUri, auth);
        return;
      }

      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  // A redirect target we do not recognise is shown, never followed. It means
  // either a teammate's service is misconfigured or someone is trying to have
  // the portal deliver a token somewhere it does not belong.
  if (rejected) {
    return (
      <AuthShell
        title="That return address is not allowed"
        subtitle="Signing in here would send your access token somewhere Code Guru does not recognise, so the portal stopped."
      >
        <p className="auth-error">Rejected: {requested}</p>
        <p className="auth-hint">
          If this is one of our services, add its origin to
          <code> VITE_ALLOWED_REDIRECTS</code> in the portal environment.
        </p>
        <Link className="auth-button auth-button-secondary" to="/login">
          Continue to the portal instead
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle={
        redirectUri
          ? 'You will be returned to ' + new URL(redirectUri).host + ' afterwards.'
          : null
      }
      footer={
        <span>
          No account yet?{' '}
          <Link to={'/register' + location.search}>Create one</Link>
        </span>
      }
    >
      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        {error && <p className="auth-error">{error}</p>}

        <label htmlFor="identifier">Email or username</label>
        <input
          id="identifier"
          name="identifier"
          type="text"
          autoComplete="username"
          required
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          placeholder="you@example.com"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button className="auth-button" type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </AuthShell>
  );
}
