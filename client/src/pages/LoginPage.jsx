import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { GitHubIcon } from '../components/Icons';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const { loginUrl, loginWithTokens, authError } = useAuth();
  const [localError, setLocalError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const access = searchParams.get('access');
    const refresh = searchParams.get('refresh');
    if (access && refresh) {
      const handleAutoLogin = async () => {
        try {
          await loginWithTokens({ access, refresh });
          navigate('/home', { replace: true });
        } catch (error) {
          setLocalError('Auto-login failed: ' + error.message);
        }
      };

      handleAutoLogin();
    }
  }, [searchParams, loginWithTokens, navigate]);

  return (
    <div className="auth-grid">
      <div className="auth-hero">
        <div className="pill">Secure Authentication</div>
        <h1>Sign in to Visor</h1>
        <p>
          Connect GitHub to review projects, verify changes, and get focused AI
          assistance when your team needs a second set of eyes.
        </p>
        
        <div className="auth-actions">
          <a className="button" href={loginUrl} style={{ padding: '14px 28px', fontSize: '16px' }}>
            <GitHubIcon size={20} color="white" />
            <span>Continue with GitHub</span>
          </a>
        </div>
        
        <div style={{ marginTop: '24px' }}>
          <Link className="subtle" to="/register">
            Don&apos;t have an account? <span style={{ color: 'var(--accent-500)', fontWeight: 600 }}>Register here</span>
          </Link>
        </div>

        {localError || authError ? (
          <div className="section-card" style={{ marginTop: '24px', borderColor: 'rgba(255, 0, 0, 0.2)', background: 'rgba(255, 0, 0, 0.02)' }}>
            <p style={{ color: '#d32f2f', margin: 0, fontSize: '14px' }}>
              {localError || authError}
            </p>
          </div>
        ) : null}
      </div>

      <div className="auth-card">
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <div className="github-mark" style={{ margin: '0 auto 16px', width: '64px', height: '64px', borderRadius: '20px' }}>
            <GitHubIcon size={32} color="white" />
          </div>
          <h3>Ready to Check</h3>
          <p className="subtle">
            Visor keeps your repositories, findings, and AI review sessions close
            enough for fast hackathon decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
