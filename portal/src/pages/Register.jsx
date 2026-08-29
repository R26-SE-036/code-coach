import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import AuthShell from '../components/AuthShell.jsx';
import { register, saveTokens } from '../lib/codeguru-auth.js';
import { buildHandoffUrl, resolveRedirectUri } from '../lib/handoff.js';
import { ALLOWED_REDIRECTS, CLIENT_NAME, CODE_COACH_URL } from '../config.js';

/**
 * Registration for the whole platform. One account works in the VS Code
 * extension, Study Guider and PairPath.
 *
 * Code Coach stores a single `full_name`, so that is what is collected here.
 * PairPath splits it into firstName/lastName on its side — that split is its
 * business, and doing it here would push a PairPath schema detail into the
 * shared form.
 */
export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
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

    // Checked here rather than server-side because only this form knows the
    // student typed it twice.
    if (password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setError('Use at least 8 characters for your password.');
      return;
    }

    setBusy(true);
    try {
      const auth = await register(CODE_COACH_URL, {
        fullName: fullName.trim(),
        email: email.trim(),
        password,
        clientName: CLIENT_NAME,
      });

      saveTokens(auth);

      if (redirectUri) {
        window.location.href = buildHandoffUrl(redirectUri, auth);
        return;
      }

      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  if (rejected) {
    return (
      <AuthShell
        title="That return address is not allowed"
        subtitle="Registering here would send your access token somewhere Code Guru does not recognise, so the portal stopped."
      >
        <p className="auth-error">Rejected: {requested}</p>
        <Link className="auth-button auth-button-secondary" to="/register">
          Continue to the portal instead
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="One account for every part of Code Guru."
      footer={
        <span>
          Already registered? <Link to={'/login' + location.search}>Sign in</Link>
        </span>
      }
    >
      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        {error && <p className="auth-error">{error}</p>}

        <label htmlFor="full_name">Full name</label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          required
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          placeholder="Jane Student"
        />

        <label htmlFor="email">Email address</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="student@example.com"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <label htmlFor="confirm_password">Confirm password</label>
        <input
          id="confirm_password"
          name="confirm_password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />

        <button className="auth-button" type="submit" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  );
}
