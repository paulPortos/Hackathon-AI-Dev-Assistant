import { Link } from 'react-router-dom';
import { GitHubIcon } from '../components/Icons';

export default function AuthLandingPage() {
  return (
    <div className="auth-grid">
      <div className="auth-hero">
        <div className="pill">Next-Gen Dev Console</div>
        <h1>Build Faster, Audit Smarter</h1>
        <p>
          Khaki Console integrates your GitHub workflow with advanced AI agents. 
          Monitor security, track progress, and collaborate with your senior AI 
          developer in one seamless interface.
        </p>
        <div className="auth-actions">
          <Link className="button" to="/login" style={{ padding: '14px 28px', fontSize: '16px' }}>
            Get Started
          </Link>
          <Link className="button ghost" to="/register" style={{ padding: '14px 28px', fontSize: '16px' }}>
            Learn More
          </Link>
        </div>
      </div>
      <div className="auth-card" style={{ padding: '32px' }}>
        <div className="auth-mark">
          <div className="github-mark" style={{ width: '48px', height: '48px', borderRadius: '14px' }}>
            <GitHubIcon size={24} color="white" />
          </div>
          <div>
            <h3 style={{ margin: 0 }}>GitHub Native</h3>
            <p className="subtle" style={{ margin: 0 }}>Instant sync, no password required.</p>
          </div>
        </div>
        
        <div style={{ marginTop: '24px', display: 'grid', gap: '16px' }}>
          <div className="section-card" style={{ background: 'white', boxShadow: 'none', border: '1px solid rgba(0,0,0,0.05)' }}>
             <h4 style={{ margin: '0 0 8px' }}>Security First</h4>
             <p className="subtle" style={{ margin: 0 }}>Automated vulnerability scanning and reporting for every project.</p>
          </div>
          <div className="section-card" style={{ background: 'white', boxShadow: 'none', border: '1px solid rgba(0,0,0,0.05)' }}>
             <h4 style={{ margin: '0 0 8px' }}>AI Collaboration</h4>
             <p className="subtle" style={{ margin: 0 }}>Chat with a Senior AI agent that understands your codebase and goals.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
