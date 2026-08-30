import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import CodeGuruBar from '../components/CodeGuruBar.jsx';
import {
  authorizedFetch,
  clearTokens,
  loadTokens,
  loadUser,
  logout,
  me,
} from '../lib/codeguru-auth.js';
import { configuredServices, handOffTo } from '../lib/services.js';
import { CODE_COACH_URL } from '../config.js';

/**
 * Home — where a signed-in student lands, and the only page that shows the
 * whole platform at once.
 *
 * The numbers are not decoration. Code Coach already aggregates every
 * component's activity into GET /api/v1/dashboard/me/overview, so each card can
 * carry a live count from the service it links to, and the activity feed shows
 * all four services writing to one student record. That is the integration
 * demonstrating itself rather than being asserted.
 *
 * The overview is fetched fail-soft: if Code Coach is unreachable the cards
 * still render and still navigate, they just lose their counts. Losing a number
 * should not cost the student the ability to get to a service.
 */

const MASTERY_WORDS = [
  ['strong_count', 'strong'],
  ['developing_count', 'developing'],
  ['at_risk_count', 'at risk'],
];

/** "2 concepts strong, 1 at risk" — or nothing at all before any activity. */
function masterySummary(mastery) {
  if (!mastery) return '';
  const parts = MASTERY_WORDS
    .filter(([key]) => (mastery[key] ?? 0) > 0)
    .map(([key, word]) => mastery[key] + ' ' + word);
  if (!parts.length) return '';
  return parts.join(' · ');
}

function relativeTime(iso) {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return minutes + 'm ago';
  const hours = Math.round(minutes / 60);
  if (hours < 24) return hours + 'h ago';
  return Math.round(hours / 24) + 'd ago';
}

/** "adaptive_gamification" -> "Gamification" */
function componentLabel(component) {
  const words = String(component || '').replace(/_/g, ' ').trim();
  if (!words) return 'Platform';
  if (words.startsWith('adaptive ')) return 'Gamification';
  return words.replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Hub() {
  const [user, setUser] = useState(loadUser());
  const [overview, setOverview] = useState(null);
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

  // Fail-soft, deliberately: an unreachable Code Coach costs the counts, not
  // the page.
  useEffect(() => {
    let cancelled = false;
    authorizedFetch(
      CODE_COACH_URL + '/api/v1/dashboard/me/overview?concept_limit=5&timeline_limit=8',
      {},
      { codeCoachUrl: CODE_COACH_URL },
    )
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!cancelled && payload) setOverview(payload);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSignOut() {
    const { accessToken } = loadTokens();
    if (accessToken) await logout(CODE_COACH_URL, accessToken);
    clearTokens();
    navigate('/login', { replace: true });
  }

  function openService(serviceUrl) {
    const failure = handOffTo(serviceUrl, user);
    if (failure) setError(failure);
  }

  const counts = overview?.counts || {};
  const timeline = overview?.recent_timeline || [];
  const summary = masterySummary(overview?.mastery);
  const firstName = String(user?.full_name || '').trim().split(' ')[0];

  return (
    <>
      <CodeGuruBar service="home" portalUrl="" user={user} onSignOut={handleSignOut} />

      <div className="hub-page">
        <header className="hub-header">
          <div>
            <h1>{firstName ? 'Welcome back, ' + firstName : 'Welcome back'}</h1>
            <p>
              {summary
                ? summary + ' across ' + (overview?.mastery?.total_concepts ?? 0) + ' concepts'
                : 'Sign in to a service below to start building your learning record.'}
            </p>
          </div>
        </header>

        {error && <p className="auth-error">{error}</p>}

        <div className="hub-grid">
          {/* Code Coach has no web UI of its own — it is the VS Code extension —
              so its card reports what it has collected and points at the IDE
              rather than navigating. */}
          <div className="hub-card hub-card-static">
            <h2>Code Coach</h2>
            <p>
              Live diagnostics while you write Java. Everything the other three services
              react to starts here.
            </p>
            <span className="hub-card-count">
              {counts.total_diagnostics ?? '—'} <small>diagnostics</small>
            </span>
            <span className="hub-card-go hub-card-go-muted">Runs in VS Code</span>
          </div>

          {configuredServices().map((service) => (
            <button
              key={service.key}
              className="hub-card"
              onClick={() => openService(service.url)}
            >
              <h2>{service.name}</h2>
              <p>{service.description}</p>
              <span className="hub-card-count">
                {counts[service.countKey] ?? '—'} <small>{service.countLabel}</small>
              </span>
              <span className="hub-card-go">Open →</span>
            </button>
          ))}
        </div>

        {timeline.length > 0 && (
          <section className="hub-activity">
            <h3>Recent activity</h3>
            <ul className="hub-timeline">
              {timeline.map((item) => (
                <li key={item.event_id} className="hub-timeline-item">
                  <span className="hub-timeline-tag">{componentLabel(item.component)}</span>
                  <div>
                    <div className="hub-timeline-title">{item.title}</div>
                    <div className="hub-timeline-sub">{item.summary}</div>
                  </div>
                  <span className="hub-timeline-time">{relativeTime(item.occurred_at)}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </>
  );
}
