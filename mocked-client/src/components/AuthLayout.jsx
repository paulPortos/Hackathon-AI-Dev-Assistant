import { NavLink, Outlet } from 'react-router-dom';
import { GitHubIcon } from './Icons';

export default function AuthLayout() {
  return (
    <div className="auth-shell">
      <header className="auth-header" style={{ borderBottom: '1px solid rgba(0,0,0,0.05)', background: 'rgba(255,255,255,0.5)', backdropFilter: 'blur(10px)' }}>
        <div className="brand">
          <span style={{ color: 'var(--accent-500)' }}>Visor</span>
        </div>
        <nav className="auth-links">
          <NavLink to="/login" className={({ isActive }) => (isActive ? 'active' : '')}>
            Sign In
          </NavLink>
          <NavLink to="/register" className={({ isActive }) => (isActive ? 'active' : '')}>
            Get Started
          </NavLink>
          <div style={{ marginLeft: '12px', paddingLeft: '12px', borderLeft: '1px solid rgba(0,0,0,0.1)' }}>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="button ghost" style={{ padding: '6px' }}>
              <GitHubIcon size={16} />
            </a>
          </div>
        </nav>
      </header>
      <main className="auth-content">
        <Outlet />
      </main>
      <footer className="footer" style={{ background: 'transparent' }}>
        <p className="subtle">© 2026 Visor • Ready to review, check, and assist</p>
      </footer>
    </div>
  );
}
