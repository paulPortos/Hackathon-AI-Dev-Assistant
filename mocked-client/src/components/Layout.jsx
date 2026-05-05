import { NavLink, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { GitHubIcon } from './Icons';

export default function Layout() {
  const { user, accessToken, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand" style={{ marginBottom: '40px' }}>
          undefined
        </div>
        <nav className="side-links">
          <NavLink to="/home" className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/projects" className={({ isActive }) => (isActive ? 'active' : '')}>
            Workspace
          </NavLink>
          <NavLink to="/senior" className={({ isActive }) => (isActive ? 'active' : '')}>
            Senior AI
          </NavLink>
        </nav>
        <div className="side-footer">
          <div className="stat-card" style={{ padding: '12px', background: 'rgba(255,255,255,0.5)' }}>
            <p className="subtle" style={{ fontSize: '11px', marginBottom: '4px' }}>Session Status</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: accessToken ? '#4caf50' : '#f44336' }}></div>
              <span style={{ fontSize: '12px', fontWeight: 600 }}>{accessToken ? 'Authenticated' : 'Guest'}</span>
            </div>
          </div>
          
          <div className="profile-row" style={{ marginTop: '12px', marginBottom: '8px' }}>
            <div className="avatar" style={{ width: '28px', height: '28px', borderRadius: '8px', fontSize: '11px' }}>
              {(user?.username || 'U').charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ margin: 0, fontSize: '12px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.name || user?.username || 'Guest User'}
              </p>
            </div>
          </div>

          <button 
            className="button ghost" 
            style={{ width: '100%', fontSize: '11px', padding: '6px', opacity: 0.8, border: '1px solid rgba(0,0,0,0.05)' }} 
            type="button" 
            onClick={logout}
          >
            Sign Out
          </button>
        </div>
      </aside>
      <div className="app-main">
        <header className="app-header">
          <div>
            <p className="subtle">Current View</p>
            <strong style={{ fontSize: '18px' }}>
              {location.pathname.substring(1).charAt(0).toUpperCase() + location.pathname.substring(2)}
            </strong>
          </div>
          <div className="header-actions">
             <a href="https://github.com" target="_blank" rel="noreferrer" className="button ghost" style={{ borderRadius: '12px', padding: '8px' }}>
               <GitHubIcon size={18} />
             </a>
             <div className="avatar" style={{ width: '40px', height: '40px', cursor: 'pointer' }}>
               {(user?.username || 'U').charAt(0).toUpperCase()}
             </div>
          </div>
        </header>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
