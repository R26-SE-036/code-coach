import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  clearTokens,
  loadTokens,
  loadUser,
  logout,
  me,
} from '../lib/codeguru-auth.js';
import {
  buildHandoffUrl,
  isAllowedRedirect,
  parseAllowedOrigins,
} from '../lib/handoff.js';
import {
  ALLOWED_REDIRECTS,
  CODE_COACH_URL,
  PAIRPATH_URL,
  STUDY_GUIDER_URL,
} from '../config.js';

/**
 * Where a signed-in student goes next.
 *
 * Following a link from here carries the session with it, so the student signs
 * in once and lands inside Study Guider or PairPath already authenticated.
 */
export default function Hub() {
  const [user, setUser] = useState(loadUser());
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // The stored user may be stale, or may be nothing more than the user_id
  // recovered from a handoff fragment. /auth/me is the authoritative answer and
  // doubles as a check that the session is still valid server-side.
  useEffect(() => {
    const { accessToken } = loadTokens();
    if (!accessToken) return;

    let cancelled = false;
    me(CODE_COACH_URL, accessToken)
      .then((response) => {
        if (!cancelled) setUser(response.user);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          clearTokens();
          navigate('/login', { replace: true });
        } else {
          setError(err.message);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [navigate]);

  async function handleSignOut() {
    const { accessToken } = loadTokens();
    if (accessToken) await logout(CODE_COACH_URL, accessToken);
    clearTokens();
    navigate('/login', { replace: true });
  }

  /**
   * Open a sibling service with the session attached.
   *
   * The destination is checked against the same allow-list the login redirect
   * uses. It is configuration rather than user input, but a typo in
   * VITE_PAIRPATH_URL should fail visibly here rather than quietly post a
   * token to whatever that typo resolves to.
   */
  function openService(serviceUrl) {
    const allowed = parseAllowedOrigins(ALLOWED_REDIRECTS);
    if (!isAllowedRedirect(serviceUrl, allowed)) {
      setError(
        serviceUrl + ' is not in VITE_ALLOWED_REDIRECTS, so the portal will not send your token there.',
      );
      return;
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
  }

  const services = [
    {
      name: 'Study Guider',
      url: STUDY_GUIDER_URL,
      description: 'Micro-lessons and quizzes for the concepts you keep getting stuck on.',
    },
    {
      name: 'PairPath',
      url: PAIRPATH_URL,
      description: 'Pair programming sessions with live coaching and peer review.',
    },
  ].filter((service) => service.url);

  return (
    <div className="hub-page">
      <header className="hub-header">
        <div>
          <h1>Code Guru</h1>
          <p>
            Signed in as <strong>{user?.full_name || user?.email || user?.user_id || '…'}</strong>
          </p>
        </div>
        <button className="auth-button auth-button-secondary" onClick={handleSignOut}>
          Sign out
        </button>
      </header>

      {error && <p className="auth-error">{error}</p>}

      <div className="hub-grid">
        {services.map((service) => (
          <button key={service.name} className="hub-card" onClick={() => openService(service.url)}>
            <h2>{service.name}</h2>
            <p>{service.description}</p>
            <span className="hub-card-go">Open →</span>
          </button>
        ))}
      </div>

      <section className="hub-note">
        <h3>Code Coach</h3>
        <p>
          Code Coach runs inside VS Code. Install the extension and sign in with this same
          account — the errors it finds while you code are what drive your Study Guider
          lessons.
        </p>
      </section>
    </div>
  );
}
