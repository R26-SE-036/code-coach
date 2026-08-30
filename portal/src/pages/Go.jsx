/**
 * /go?to=<service-key> — the hop every CodeGuruBar link makes.
 *
 * A student in Study Guider clicking "PairPath" cannot be sent straight there:
 * the two run on different origins, so the session in Study Guider's
 * localStorage is invisible to PairPath. This route is the shared middle
 * ground. It resolves the key against the portal's registry and reuses the same
 * allow-listed handoff the Home page uses, so the student lands already signed
 * in.
 *
 * It renders almost nothing on purpose — in the normal case the redirect fires
 * from the first effect and this page is never seen.
 */
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { loadUser } from '../lib/codeguru-auth.js';
import { handOffTo, serviceByKey } from '../lib/services.js';

export default function Go() {
  const [params] = useSearchParams();
  const [error, setError] = useState('');
  const key = params.get('to') || '';

  useEffect(() => {
    const service = serviceByKey(key);
    if (!service) {
      setError('Unknown service "' + key + '".');
      return;
    }
    // Empty string means the redirect is under way.
    const failure = handOffTo(service.url, loadUser());
    if (failure) setError(failure);
  }, [key]);

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark">CG</div>
          <div>
            <h1>Code Guru</h1>
            <p>{error ? 'Could not open that service' : 'Taking you there…'}</p>
          </div>
        </div>

        {error && (
          <>
            <p className="auth-error">{error}</p>
            <Link className="auth-button auth-button-secondary" to="/">
              Back to Home
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
