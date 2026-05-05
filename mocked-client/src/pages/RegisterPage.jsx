import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { GitHubIcon } from '../components/Icons';

export default function RegisterPage() {
  const { loginUrl, loginWithCallbackPayload, loginWithTokens, authError } = useAuth();
  const [payloadText, setPayloadText] = useState('');
  const [manualAccess, setManualAccess] = useState('');
  const [manualRefresh, setManualRefresh] = useState('');
  const [localError, setLocalError] = useState('');
  const [showDevOptions, setShowDevOptions] = useState(false);
  const navigate = useNavigate();

  const handlePayload = async () => {
    setLocalError('');
    try {
      await loginWithCallbackPayload(payloadText);
      navigate('/home');
    } catch (error) {
      setLocalError(error.message);
    }
  };

  return (
    <div className="auth-grid">
      <div className="auth-hero">
        <div className="pill">New Workspace</div>
        <h1>Join Khaki</h1>
        <p>
          Create your account by connecting GitHub. We&apos;ll automatically sync your
          repositories and profile settings.
        </p>
        
        <div className="auth-actions">
          <a className="button" href={loginUrl} style={{ padding: '14px 28px', fontSize: '16px' }}>
            <GitHubIcon size={20} color="white" />
            <span>Register with GitHub</span>
          </a>
        </div>
        
        <div style={{ marginTop: '24px' }}>
          <Link className="subtle" to="/login">
            Already have an account? <span style={{ color: 'var(--accent-500)', fontWeight: 600 }}>Login here</span>
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
          <div className="github-mark" style={{ margin: '0 auto 16px', width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, var(--accent-500), var(--accent-300))' }}>
            <GitHubIcon size={32} color="white" />
          </div>
          <h3>Seamless Onboarding</h3>
          <p className="subtle">One-click registration. No passwords to remember.</p>
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
          </div>
        )}
      </div>
    </div>
  );
}
