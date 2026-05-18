import { Link } from 'react-router-dom';
import { GitHubIcon } from '../components/Icons';

export default function AuthLandingPage() {
  return (
    <div className="auth-grid">
      <div className="auth-hero">
        <div className="pill">Project Review Console</div>
        <h1>Meet Visor</h1>
        <p>
          Visor connects your GitHub workflow with focused AI review, project
          context, and team-ready findings so you can check changes and move with
          confidence.
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
             <h4 style={{ margin: '0 0 8px' }}>Review Ready</h4>
             <p className="subtle" style={{ margin: 0 }}>Surface project risks, tasks, and repository context before demo time.</p>
          </div>
          <div className="section-card" style={{ background: 'white', boxShadow: 'none', border: '1px solid rgba(0,0,0,0.05)' }}>
             <h4 style={{ margin: '0 0 8px' }}>Assisted Delivery</h4>
             <p className="subtle" style={{ margin: 0 }}>Ask the Senior AI agent to verify claims and hand off useful work.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
