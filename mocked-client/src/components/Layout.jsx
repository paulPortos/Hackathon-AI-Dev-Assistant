import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { GitHubIcon } from './Icons';

export default function Layout() {
  const { user, accessToken, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand" style={{ marginBottom: '40px' }}>
          Visor
        </div>
        <nav className="side-links">
          <NavLink to="/home" className={({ isActive }) => (isActive ? 'active' : '')}>
            Overview
          </NavLink>
          <NavLink to="/projects" className={({ isActive }) => (isActive ? 'active' : '')}>
            Workspace
          </NavLink>
          <NavLink to="/senior" className={({ isActive }) => (isActive ? 'active' : '')}>
            Senior AI
          </NavLink>
          <NavLink to="/kanban" className={({ isActive }) => (isActive ? 'active' : '')}>
            Kanban Board
          </NavLink>
          <NavLink to="/calendar" className={({ isActive }) => (isActive ? 'active' : '')}>
            Calendar
          </NavLink>
          <NavLink to="/scrum-live" className={({ isActive }) => (isActive ? 'active' : '')}>
            Scrum Live
          </NavLink>
        </nav>
        <div className="side-footer">
          <NavLink
            to={accessToken ? '/profile' : '/login'}
            className="profile-row"
            style={{
              marginBottom: '8px',
              textDecoration: 'none',
              color: 'inherit',
              padding: '10px',
              borderRadius: '12px',
              background: 'rgba(255,255,255,0.5)',
            }}
          >
            <div className="avatar" style={{ width: '28px', height: '28px', borderRadius: '8px', fontSize: '11px' }}>
              {(user?.username || 'U').charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ margin: 0, fontSize: '12px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.name || user?.username || 'Guest User'}
              </p>
              <p className="subtle" style={{ margin: 0, fontSize: '11px' }}>
                {accessToken ? 'View profile' : 'Sign in'}
              </p>
            </div>
          </NavLink>

          <button 
            className="button ghost" 
            style={{ width: '100%', fontSize: '11px', padding: '6px', opacity: 0.8, border: '1px solid rgba(0,0,0,0.05)' }} 
            type="button" 
            onClick={handleLogout}
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
        <main className={`app-content ${location.pathname === '/kanban' ? 'full-width' : ''}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
