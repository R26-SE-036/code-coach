import { Navigate, Route, Routes } from 'react-router-dom';

import { isSignedIn } from './lib/codeguru-auth.js';
import { devLoginEnabled } from './lib/codeguru-auth.js';
import { DEV_LOGIN_FLAG } from './config.js';

import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Hub from './pages/Hub.jsx';
import DevLogin from './pages/DevLogin.jsx';
import Go from './pages/Go.jsx';

/**
 * The hub is the only page that requires a session. Login and register must
 * stay reachable signed out, and they keep their query string (redirect_uri)
 * on the way through — losing it would strand the student on the portal
 * instead of sending them back to the service they came from.
 */
function RequireAuth({ children }) {
  if (!isSignedIn()) {
    return <Navigate to={'/login' + window.location.search} replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireAuth>
            <Hub />
          </RequireAuth>
        }
      />
      {/* Where every CodeGuruBar service link lands: resolve the key, then
          hand the session over. Needs a session, like the Home page. */}
      <Route
        path="/go"
        element={
          <RequireAuth>
            <Go />
          </RequireAuth>
        }
      />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/*
        Localhost-only sign-in for working on the portal itself. The route is
        not even registered unless both guards pass, so in a deployed build it
        404s to the catch-all rather than rendering a second login page.
      */}
      {devLoginEnabled(DEV_LOGIN_FLAG) && (
        <Route path="/dev-login" element={<DevLogin />} />
      )}

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
