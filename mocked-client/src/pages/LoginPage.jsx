import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { GitHubIcon } from '../components/Icons';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const { loginUrl, loginWithCallbackPayload, loginWithTokens, authError } = useAuth();
  const [payloadText, setPayloadText] = useState('');
  const [manualAccess, setManualAccess] = useState('');
  const [manualRefresh, setManualRefresh] = useState('');
  const [localError, setLocalError] = useState('');
  const [showDevOptions, setShowDevOptions] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const access = searchParams.get('access');
    const refresh = searchParams.get('refresh');
    if (access && refresh) {
      handleAutoLogin(access, refresh);
    }
  }, [searchParams]);

  const handleAutoLogin = async (access, refresh) => {
    try {
      await loginWithTokens({ access, refresh });
      navigate('/home');
    } catch (error) {
      setLocalError('Auto-login failed: ' + error.message);
    }
  };

  const handlePayload = async () => {
    setLocalError('');
    try {
      await loginWithCallbackPayload(payloadText);
      navigate('/home');
    } catch (error) {
      setLocalError(error.message);
    }
  };

  const handleManual = async () => {
    setLocalError('');
    try {
      await loginWithTokens({ access: manualAccess, refresh: manualRefresh });
      navigate('/home');
    } catch (error) {
      setLocalError(error.message);
    }
  };

  return (
    <div className="auth-grid">
      <div className="auth-hero">
        <div className="pill">Secure Authentication</div>
        <h1>Sign in to Khaki</h1>
        <p>
          Connect your GitHub account to access your workspace, manage projects, and
          collaborate with senior AI developers.
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
          <h3>Enterprise Ready</h3>
          <p className="subtle">Fast, secure, and integrated with your existing workflow.</p>
        </div>

        <div className="auth-divider" style={{ cursor: 'pointer', userSelect: 'none' }} onClick={() => setShowDevOptions(!showDevOptions)}>
          {showDevOptions ? '▼ Hide Developer Options' : '▶ Show Developer Options'}
        </div>

        {showDevOptions && (
          <div style={{ animation: 'riseIn 0.3s ease both' }}>
            <div className="field">
              <label className="label">Callback JSON Payload</label>
              <textarea
                className="textarea"
                value={payloadText}
                onChange={(e) => setPayloadText(e.target.value)}
                placeholder='{"access":"...","refresh":"..."}'
                style={{ minHeight: '80px' }}
              />
              <button className="button secondary" onClick={handlePayload} style={{ marginTop: '8px', width: '100%' }}>
                Apply JSON
              </button>
            </div>
            
            <div className="auth-divider">Manual Tokens</div>
            
            <div className="field">
              <input
                className="input"
                value={manualAccess}
                onChange={(e) => setManualAccess(e.target.value)}
                placeholder="Access Token"
              />
            </div>
            <div className="field">
              <input
                className="input"
                value={manualRefresh}
                onChange={(e) => setManualRefresh(e.target.value)}
                placeholder="Refresh Token"
              />
            </div>
            <button className="button ghost" onClick={handleManual} style={{ width: '100%' }}>
              Save Tokens
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
