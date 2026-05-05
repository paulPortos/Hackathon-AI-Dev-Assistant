import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import { GitHubIcon } from '../components/Icons';

const defaultGreeting =
  'Good day. How are you today, and may I know your progress and what you have completed so far?';

const defaultChoices = ['Progress update', 'Blocker report', 'Request a review'];

export default function SeniorPage() {
  const [searchParams] = useSearchParams();
  const initialProjectId = searchParams.get('projectId') || '';

  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('main');
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');

  const loadSessions = async () => {
    setStatus('loading');
    try {
      const payload = await api.listSeniorSessions();
      const data = normalizeList(payload);
      setSessions(data);
      setStatus('ready');
      return data;
    } catch (err) {
      setError(err.message);
      setStatus('error');
      return [];
    }
  };

  const loadBranches = async (pId) => {
    try {
      const payload = await api.listProjectBranches(pId);
      setBranches(payload.branches || []);
      if (payload.default_branch) setSelectedBranch(payload.default_branch);
    } catch (err) {
      console.error('Failed to load branches', err);
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      const payload = await api.listSeniorMessages(sessionId);
      setMessages(normalizeList(payload));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateSession = async (pId, bName = 'main') => {
    try {
      const payload = await api.createSeniorSession({
        project_id: Number(pId),
        commit_sha: 'latest',
        branch_name: bName,
      });
      setSessions((prev) => [payload, ...prev]);
      setSelectedSessionId(String(payload.id));
    } catch (err) {
      setError('Session creation failed: ' + err.message);
    }
  };

  useEffect(() => {
    const init = async () => {
      const currentSessions = await loadSessions();
      if (initialProjectId) {
        await loadBranches(initialProjectId);
        // If a projectId is provided, try to find an existing active session or create a new one
        const existing = currentSessions.find(s => String(s.project_id) === initialProjectId);
        if (existing) {
          setSelectedSessionId(String(existing.id));
        } else {
          // We'll let the user click "Start" if they want a different branch, 
          // or just default to main for now.
          await handleCreateSession(initialProjectId, 'main');
        }
      } else if (currentSessions.length > 0) {
        setSelectedSessionId(String(currentSessions[0].id));
      }
    };
    init();
  }, [initialProjectId]);

  useEffect(() => {
    if (selectedSessionId) {
      loadMessages(selectedSessionId);
    }
  }, [selectedSessionId]);

  const sendChoice = async (choiceText) => {
    if (!selectedSessionId) return;
    try {
      await api.sendSeniorMessage(selectedSessionId, {
        input_type: 'choice',
        choice: choiceText,
        choice_payload: { source: 'ui' },
      });
      await loadMessages(selectedSessionId);
    } catch (err) {
      setError(err.message);
    }
  };

  const sendText = async () => {
    if (!selectedSessionId || !inputText.trim()) return;
    try {
      const textToSend = inputText;
      setInputText('');
      await api.sendSeniorMessage(selectedSessionId, {
        input_type: 'open_text',
        text: textToSend,
      });
      await loadMessages(selectedSessionId);
    } catch (err) {
      setError(err.message);
    }
  };

  const sendAudio = async () => {
    if (!selectedSessionId || !audioFile) return;
    const formData = new FormData();
    formData.append('input_type', 'audio');
    formData.append('audio', audioFile);
    try {
      setAudioFile(null);
      await api.sendSeniorMessage(selectedSessionId, formData, true);
      await loadMessages(selectedSessionId);
    } catch (err) {
      setError(err.message);
    }
  };

  const lastAssistant = [...messages]
    .reverse()
    .find((message) => message.role === 'assistant');

  const choices = useMemo(() => {
    const payloadChoices = lastAssistant?.structured_payload?.choices;
    if (Array.isArray(payloadChoices) && payloadChoices.length) {
      return payloadChoices;
    }
    return defaultChoices;
  }, [lastAssistant]);

  return (
    <div className="senior-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '32px', height: 'calc(100vh - 180px)' }}>
      {/* LEFT COLUMN: CHAT AREA */}
      <section style={{ display: 'flex', flexDirection: 'column', background: 'var(--surface)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        <div className="chat-header" style={{ padding: '20px 24px', borderBottom: '1px solid rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ margin: 0 }}>Senior AI Assistant</h3>
            <p className="subtle" style={{ margin: 0, fontSize: '12px' }}>Choice-driven development partner</p>
          </div>
          {error && <span className="tag" style={{ background: '#ffebee', color: '#c62828' }}>{error}</span>}
        </div>

        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {messages.length === 0 ? (
            <div className="message-bubble assistant">
              <div className="avatar">AI</div>
              <div className="text">{defaultGreeting}</div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`message-bubble ${message.role === 'assistant' ? 'assistant' : 'user'}`}>
                <div className="avatar">{message.role === 'assistant' ? 'AI' : 'U'}</div>
                <div className="content">
                  <div className="text">{message.text_content}</div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="chat-input-area" style={{ padding: '24px', background: 'rgba(0,0,0,0.02)', borderTop: '1px solid rgba(0,0,0,0.05)' }}>
          <div className="input-group" style={{ position: 'relative' }}>
            <textarea
              className="textarea"
              style={{ paddingRight: '100px', minHeight: '80px', borderRadius: 'var(--radius-md)', background: 'white' }}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Write a message..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendText();
                }
              }}
            />
            <button className="button secondary" onClick={sendText} style={{ position: 'absolute', right: '12px', bottom: '12px' }}>
              Send
            </button>
          </div>

          <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <input
              type="file"
              id="audio-upload"
              style={{ display: 'none' }}
              onChange={(e) => {
                setAudioFile(e.target.files?.[0]);
                if (e.target.files?.[0]) sendAudio();
              }}
            />
            <label htmlFor="audio-upload" className="button ghost" style={{ cursor: 'pointer', fontSize: '12px' }}>
              🎤 Send Voice
            </label>
            {audioFile && <span className="subtle" style={{ fontSize: '12px' }}>{audioFile.name}</span>}
          </div>
        </div>
      </section>

      {/* RIGHT COLUMN: SIDEBAR */}
      <aside style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius-md)', padding: '24px', border: '1px solid rgba(0,0,0,0.05)' }}>
          <h4 style={{ margin: '0 0 16px' }}>Session Settings</h4>
          
          <div className="field">
            <label className="label" style={{ fontSize: '12px' }}>Project Branch</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <select 
                className="select" 
                value={selectedBranch} 
                onChange={(e) => setSelectedBranch(e.target.value)}
                style={{ flex: 1 }}
              >
                {branches.map(b => (
                  <option key={b.name} value={b.name}>{b.name}</option>
                ))}
                {branches.length === 0 && <option value="main">main</option>}
              </select>
              <button 
                className="button secondary" 
                style={{ padding: '8px' }}
                onClick={() => initialProjectId && handleCreateSession(initialProjectId, selectedBranch)}
                title="Start New Session"
              >
                +
              </button>
            </div>
          </div>

          <div className="field" style={{ marginTop: '16px' }}>
            <label className="label" style={{ fontSize: '12px' }}>Switch Session</label>
            <select 
              className="select" 
              value={selectedSessionId} 
              onChange={(e) => setSelectedSessionId(e.target.value)}
            >
              <option value="">Select a session...</option>
              {sessions.map(s => (
                <option key={s.id} value={s.id}>
                  {s.project_name || `Session ${s.id}`}
                </option>
              ))}
            </select>
          </div>
          {sessions.length === 0 && <p className="subtle" style={{ fontSize: '13px' }}>No sessions found.</p>}
        </div>

        <div style={{ flex: 1, background: 'var(--surface)', borderRadius: 'var(--radius-md)', padding: '24px', border: '1px solid rgba(0,0,0,0.05)', overflowY: 'auto' }}>
          <h4 style={{ margin: '0 0 16px' }}>Today</h4>
          <div className="list">
            {sessions.slice(0, 5).map(session => (
              <div 
                key={session.id} 
                className={`session-item ${selectedSessionId === String(session.id) ? 'active' : ''}`}
                onClick={() => setSelectedSessionId(String(session.id))}
                style={{ 
                  padding: '12px', 
                  borderRadius: 'var(--radius-sm)', 
                  cursor: 'pointer',
                  background: selectedSessionId === String(session.id) ? 'var(--accent-100)' : 'transparent',
                  marginBottom: '8px',
                  border: '1px solid rgba(0,0,0,0.02)'
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '14px' }}>{session.project_name || 'Personal Assistant'}</div>
                <div className="subtle" style={{ fontSize: '11px' }}>{new Date(session.created_at).toLocaleTimeString()}</div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
