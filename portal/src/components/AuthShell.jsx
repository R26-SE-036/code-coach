/**
 * The frame every auth page sits in. Kept separate so the login, register and
 * dev-login forms differ only in their fields — if they start looking
 * different from each other, students stop trusting that they are the same
 * system.
 */
export default function AuthShell({ title, subtitle, badge, children, footer }) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="auth-brand-mark">CG</span>
          <div>
            <h1>Code Guru</h1>
            <p>One account for Code Coach, Study Guider, PairPath and Games</p>
          </div>
        </div>

        {badge}

        <h2>{title}</h2>
        {subtitle && <p className="auth-subtitle">{subtitle}</p>}

        {children}

        {footer && <div className="auth-footer">{footer}</div>}
      </div>
    </div>
  );
}
