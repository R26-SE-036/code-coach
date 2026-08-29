import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthShell from '../components/AuthShell.jsx';
import { login, register, saveTokens } from '../lib/codeguru-auth.js';
import { CLIENT_NAME, CODE_COACH_URL } from '../config.js';

/**
 * Localhost-only sign-in.
 *
 * Identical fields and identical calls to the real Login and Register pages —
 * it talks to the same Code Coach endpoints and stores the same tokens. The
 * only difference is that it never redirects anywhere, so you can work on the
 * portal (or any single service) without the handoff round trip.
 *
 * App.jsx does not even register this route unless devLoginEnabled() passes,
 * which needs BOTH a localhost hostname and the build flag.
 */
export default function DevLogin() {
  const [mode, setMode] = useState('login');
  const [fullName, setFullName] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const navigate = useNavigate();
  const registering = mode === 'register';

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);

    try {
      const auth = registering
        ? await register(CODE_COACH_URL, {
            fullName: fullName.trim(),
            email: identifier.trim(),
            password,
            clientName: CLIENT_NAME,
          })
        : await login(CODE_COACH_URL, {
            identifier: identifier.trim(),
            password,
            clientName: CLIENT_NAME,
          });

      saveTokens(auth);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title={registering ? 'Create a test account' : 'Local sign in'}
      subtitle={'Talking to ' + CODE_COACH_URL}
      badge={<p className="auth-badge">Localhost only — not part of the deployed platform</p>}
      footer={
        <button
          type="button"
          className="auth-link-button"
          onClick={() => {
            setMode(registering ? 'login' : 'register');
            setError('');
          }}
        >
          {registering ? 'I already have an account' : 'I need a new test account'}
        </button>
      }
    >
      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        {error && <p className="auth-error">{error}</p>}

        {registering && (
          <>
            <label htmlFor="dev_full_name">Full name</label>
            <input
              id="dev_full_name"
              name="full_name"
              type="text"
              required
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Jane Student"
            />
          </>
        )}

        <label htmlFor="dev_identifier">{registering ? 'Email address' : 'Email or username'}</label>
        <input
          id="dev_identifier"
          name={registering ? 'email' : 'identifier'}
          type="text"
          autoComplete="username"
          required
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          placeholder="student@example.com"
        />

        <label htmlFor="dev_password">Password</label>
        <input
          id="dev_password"
          name="password"
          type="password"
          autoComplete={registering ? 'new-password' : 'current-password'}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button className="auth-button" type="submit" disabled={busy}>
          {busy ? 'Working…' : registering ? 'Create account' : 'Sign in'}
        </button>
      </form>
    </AuthShell>
  );
}
