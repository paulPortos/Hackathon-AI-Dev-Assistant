import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { api } from '../api';
import { authStorage, normalizeList } from '../api/client';
import { WS_ROOT } from '../api/config';
import { GitHubIcon } from '../components/Icons';

const defaultGreeting =
  'Good day. How are you today, and may I know your progress and what you have completed so far?';

const defaultChoices = ['Progress update', 'Blocker report', 'Request a review'];
const findingStatusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'dismissed', label: 'Dismissed' },
  { value: 'handed_off', label: 'Handed off' },
];

const shortSha = (sha) => String(sha || '').slice(0, 7);
const TOOL_LABELS = {
  get_context: '📋 Loading project context',
  set_repository_ref: '🔗 Resolving repository ref',
  list_repository_tree: '🗂️ Scanning file tree',
  search_code: '🔍 Searching code',
  read_file: '📄 Reading file',
  compare_repository_refs: '⚖️ Comparing refs',
  get_commit_status: '✅ Checking commit status',
  find_dependency_manifests: '📦 Finding dependencies',
  prepare_pm_handoff: '📬 Preparing handoff',
};

function formatArgs(args) {
  if (!args || typeof args !== 'object') return '';
  const entries = Object.entries(args).slice(0, 2);
  return entries.map(([k, v]) => `${k}: ${String(v).slice(0, 30)}`).join(', ');
}

function ThinkingBubble({ toolEvents = [] }) {
  return (
    <div className="message-bubble assistant thinking-bubble">
      <div className="avatar">AI</div>
      <div className="thinking-body">
        {toolEvents.length > 0 ? (
          <div className="tool-log">
            {toolEvents.map((t, i) => (
              <div key={i} className={`tool-log-row status-${t.status}`}>
                <span className="tool-status-icon">
                  {t.status === 'running' ? '⟳' : t.status === 'done' ? '✓' : '✗'}
                </span>
                <span className="tool-name">{TOOL_LABELS[t.name] || t.name}</span>
                {t.args && <span className="tool-args">{formatArgs(t.args)}</span>}
                {t.duration_ms !== null && (
                  <span className="tool-duration">{t.duration_ms}ms</span>
                )}
              </div>
            ))}
          </div>
        ) : null}
        <div className="thinking-dots">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}

export default function SeniorPage() {
  const [searchParams] = useSearchParams();
  const initialProjectId = searchParams.get('projectId') || '';

  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [findings, setFindings] = useState([]);
  const [inputText, setInputText] = useState('');
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('main');
  const [sessionNameDraft, setSessionNameDraft] = useState('');
  const [findingStatusPendingId, setFindingStatusPendingId] = useState('');
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [toolEvents, setToolEvents] = useState([]);
  const [reconnectKey, setReconnectKey] = useState(0);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const autoCreatedRef = useRef(new Set());
  const pendingQueueRef = useRef([]);

  const selectedSession = useMemo(
    () => sessions.find((session) => String(session.id) === selectedSessionId),
    [sessions, selectedSessionId]
  );

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
      const list = Array.isArray(payload.branches) ? payload.branches : [];
      setBranches(list);
      if (payload.default_branch) setSelectedBranch(payload.default_branch);
      return list;
    } catch (err) {
      console.error('Failed to load branches', err);
      return [];
    }
  };

  const resolveBranchData = (branchName, branchList) => {
    const list = Array.isArray(branchList) ? branchList : branches;
    if (!list.length) {
      return { name: branchName, commitSha: '' };
    }
    const exact = list.find((branch) => branch.name === branchName);
    if (exact?.commit_sha) {
      return { name: exact.name, commitSha: exact.commit_sha };
    }
    const fallback = list.find((branch) => branch.is_default) || list[0];
    return { name: fallback?.name || branchName, commitSha: fallback?.commit_sha || '' };
  };

  const resolveSessionLabel = (session) => {
    const base = session.name || session.project_name || `Session ${session.id}`;
    const branch = session.branch_name || 'commit';
    const sha = shortSha(session.commit_sha);
    return sha ? `${base} • ${branch}@${sha}` : base;
  };

  const findSessionForBranch = (sessionList, projectId, branchData) =>
    sessionList.find(
      (session) =>
        String(session.project_id) === String(projectId) &&
        session.branch_name === branchData.name &&
        session.commit_sha === branchData.commitSha
    );

  const loadFindings = async (sessionId) => {
    try {
      const payload = await api.listSeniorFindings(sessionId);
      return normalizeList(payload);
    } catch (err) {
      setError('Findings load failed: ' + err.message);
      return [];
    }
  };

  const enqueuePendingMessage = (inputType, textContent) => {
    const clientId = `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const pendingMessage = {
      id: clientId,
      client_id: clientId,
      role: 'user',
      input_type: inputType,
      text_content: textContent,
      structured_payload: {},
      created_at: new Date().toISOString(),
      is_pending: true,
    };
    pendingQueueRef.current.push({
      clientId,
      inputType,
      textContent: textContent || '',
    });
    setMessages((prev) => [...prev, pendingMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, toolEvents]);

  const appendServerMessage = (message) => {
    if (!message) return;
    setMessages((prev) => {
      if (prev.some((item) => item.id === message.id)) return prev;

      let next = prev;
      if (message.role === 'user') {
        const queue = pendingQueueRef.current;
        if (queue.length) {
          const normalizedText = String(message.text_content || '').trim().toLowerCase();
          let matchIndex = -1;

          if (normalizedText) {
            matchIndex = queue.findIndex((item) => {
              if (item.inputType && message.input_type && item.inputType !== message.input_type) {
                return false;
              }
              return item.textContent.trim().toLowerCase() === normalizedText;
            });
          }

          if (matchIndex === -1) {
            matchIndex = queue.findIndex((item) => {
              if (item.inputType && message.input_type) {
                return item.inputType === message.input_type;
              }
              return true;
            });
          }

          if (matchIndex !== -1) {
            const [matched] = queue.splice(matchIndex, 1);
            next = next.filter((item) => item.client_id !== matched.clientId);
          }
        }
      }

      return [...next, message];
    });
  };

  const closeSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  const handleReconnect = () => {
    setError('');
    setReconnectKey((prev) => prev + 1);
  };

  const sendWsPayload = (payload) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setError('WebSocket is not connected');
      return false;
    }
    socket.send(JSON.stringify(payload));
    return true;
  };

  const mergeFindings = (incoming) => {
    if (!Array.isArray(incoming) || incoming.length === 0) return;
    setFindings((prev) => {
      const byId = new Map(prev.map((item) => [item.id, item]));
      incoming.forEach((item) => {
        if (item && item.id) {
          byId.set(item.id, item);
        }
      });
      return Array.from(byId.values()).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    });
  };

  const handleFindingStatusChange = async (finding, nextStatus) => {
    if (!selectedSessionId || !finding?.id || finding.status === nextStatus) return;
    setFindingStatusPendingId(String(finding.id));
    setError('');
    try {
      const payload = await api.updateSeniorFindingStatus(selectedSessionId, finding.id, nextStatus);
      mergeFindings([payload]);
    } catch (err) {
      setError('Finding update failed: ' + err.message);
    } finally {
      setFindingStatusPendingId('');
    }
  };

  const handleCreateSession = async (pId, bName = 'main', branchList) => {
    const resolved = resolveBranchData(bName, branchList);
    if (!resolved.commitSha) {
      setError('No commit SHA found for the selected branch. Reload branches and try again.');
      return;
    }
    try {
      const payload = await api.createSeniorSession({
        project_id: Number(pId),
        commit_sha: resolved.commitSha,
        branch_name: resolved.name,
      });
      setSessions((prev) => [payload, ...prev]);
      setSelectedSessionId(String(payload.id));
      setSelectedBranch(resolved.name);
      return payload;
    } catch (err) {
      setError('Session creation failed: ' + err.message);
      return null;
    }
  };

  const handleBranchSelect = async (branchName, branchList = branches, sessionList = sessions) => {
    setSelectedBranch(branchName);
    if (!initialProjectId) return;

    const resolved = resolveBranchData(branchName, branchList);
    if (!resolved.commitSha) {
      setError('No commit SHA found for the selected branch. Reload branches and try again.');
      return;
    }

    const matchingSession = findSessionForBranch(sessionList, initialProjectId, resolved);
    if (matchingSession) {
      setSelectedSessionId(String(matchingSession.id));
      return;
    }

    await handleCreateSession(initialProjectId, resolved.name, branchList);
  };

  const handleSessionNameSave = async () => {
    if (!selectedSessionId) return;
    const trimmed = sessionNameDraft.trim();
    const currentName = selectedSession?.name || '';
    if (trimmed === currentName) return;
    try {
      const payload = await api.updateSeniorSession(selectedSessionId, { name: trimmed });
      setSessions((prev) => prev.map((item) => (item.id === payload.id ? payload : item)));
      setSessionNameDraft(payload.name || '');
    } catch (err) {
      setError('Session rename failed: ' + err.message);
    }
  };

  useEffect(() => {
    setSessionNameDraft(selectedSession?.name || '');
    if (selectedSession?.branch_name) {
      setSelectedBranch(selectedSession.branch_name);
    }
  }, [selectedSessionId, selectedSession?.name, selectedSession?.branch_name]);

  useEffect(() => {
    const init = async () => {
      const currentSessions = await loadSessions();
      let branchList = [];
      if (initialProjectId) {
        branchList = await loadBranches(initialProjectId);
        const defaultBranchName =
          branchList.find((branch) => branch.is_default)?.name || selectedBranch || 'main';
        const resolved = resolveBranchData(defaultBranchName, branchList);
        const existing = resolved.commitSha
          ? findSessionForBranch(currentSessions, initialProjectId, resolved)
          : currentSessions.find(s => String(s.project_id) === initialProjectId);
        if (existing) {
          setSelectedSessionId(String(existing.id));
          setSelectedBranch(existing.branch_name || defaultBranchName);
        } else if (resolved.commitSha && !autoCreatedRef.current.has(`${initialProjectId}:${resolved.name}:${resolved.commitSha}`)) {
          autoCreatedRef.current.add(`${initialProjectId}:${resolved.name}:${resolved.commitSha}`);
          await handleCreateSession(initialProjectId, defaultBranchName, branchList);
        }
      } else if (currentSessions.length > 0) {
        setSelectedSessionId(String(currentSessions[0].id));
      }
    };
    init();
  }, [initialProjectId]);

  useEffect(() => {
    if (!selectedSessionId) {
      setMessages([]);
      setFindings([]);
      closeSocket();
      pendingQueueRef.current = [];
      return;
    }

    let isActive = true;

    setMessages([]);
    setFindings([]);
    setError('');
    closeSocket();

    loadFindings(selectedSessionId).then((data) => {
      if (isActive) {
        setFindings(data);
      }
    });

    const token = authStorage.getAccessToken();
    const wsUrl = token
      ? `${WS_ROOT}/sr-dev/sessions/${selectedSessionId}/?token=${encodeURIComponent(token)}`
      : `${WS_ROOT}/sr-dev/sessions/${selectedSessionId}/`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch (err) {
        return;
      }

      if (payload.event === 'history') {
        pendingQueueRef.current = [];
        setMessages(normalizeList(payload.messages));
        return;
      }

      if (payload.event === 'message' && payload.message) {
        appendServerMessage(payload.message);
        return;
      }

      if (payload.event === 'findings') {
        mergeFindings(normalizeList(payload.findings));
        return;
      }

      if (payload.event === 'error') {
        setError(payload.message || 'WebSocket error');
      }

      if (payload.event === 'tool_event') {
        setToolEvents((prev) => {
          if (payload.phase === 'start') {
            return [
              ...prev,
              {
                name: payload.name,
                args: payload.args,
                status: 'running',
                duration_ms: null,
              },
            ];
          }
          if (payload.phase === 'done') {
            return prev.map((t) =>
              t.name === payload.name && t.status === 'running'
                ? { ...t, status: payload.ok ? 'done' : 'error', duration_ms: payload.duration_ms }
                : t
            );
          }
          return prev;
        });
      }
    };

    socket.onerror = () => {
      setError('WebSocket error');
    };

    socket.onclose = (event) => {
      if (event.code === 4401) {
        setError('WebSocket unauthorized. Please sign in again.');
      } else if (event.code === 4404) {
        setError('Session not found.');
      } else if (!event.wasClean) {
        setError('WebSocket disconnected.');
      }
    };

    return () => {
      isActive = false;
      if (socketRef.current === socket) {
        socket.close();
        socketRef.current = null;
      }
    };
  }, [selectedSessionId, reconnectKey]);

  const sendChoice = async (choiceText) => {
    if (!selectedSessionId) return;
    setToolEvents([]);
    const sent = sendWsPayload({
      action: 'send_message',
      input_type: 'choice',
      choice: choiceText,
      choice_payload: { source: 'ui' },
    });
    if (sent) {
      enqueuePendingMessage('choice', choiceText);
    }
  };

  const sendText = async () => {
    if (!selectedSessionId || !inputText.trim()) return;
    setToolEvents([]);
    const textToSend = inputText.trim();
    const sent = sendWsPayload({
      action: 'send_message',
      input_type: 'open_text',
      text: textToSend,
    });
    if (sent) {
      enqueuePendingMessage('open_text', textToSend);
      setInputText('');
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

  const isThinking = useMemo(() => {
    return messages.length > 0 && messages[messages.length - 1]?.role === 'user';
  }, [messages]);

  return (
    <div className="senior-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '32px', height: 'calc(100vh - 180px)' }}>
      {/* LEFT COLUMN: CHAT AREA */}
      <section style={{ display: 'flex', flexDirection: 'column', background: 'var(--surface)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        <div className="chat-header" style={{ padding: '20px 24px', borderBottom: '1px solid rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ margin: 0 }}>Senior AI Assistant</h3>
            <p className="subtle" style={{ margin: 0, fontSize: '12px' }}>Choice-driven development partner</p>
          </div>
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="tag" style={{ background: '#ffebee', color: '#c62828' }}>{error}</span>
              {(error.includes('disconnected') || error.includes('error')) && (
                <button
                  className="button secondary"
                  onClick={handleReconnect}
                  style={{
                    padding: '4px 12px',
                    height: '28px',
                    fontSize: '11px',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}
                >
                  Reconnect
                </button>
              )}
            </div>
          )}
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
                  <div className="text">
                    {message.role === 'assistant' ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text_content}</ReactMarkdown>
                    ) : (
                      message.text_content
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          {isThinking && <ThinkingBubble toolEvents={toolEvents} />}
          <div ref={messagesEndRef} />
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
        </div>
      </section>

      {/* RIGHT COLUMN: SIDEBAR */}
      <aside style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius-md)', padding: '24px', border: '1px solid rgba(0,0,0,0.05)', maxHeight: '40vh', overflowY: 'auto' }}>
          <h4 style={{ margin: '0 0 16px' }}>Live Findings</h4>
          {findings.length === 0 ? (
            <p className="subtle" style={{ fontSize: '13px', margin: 0 }}>No findings yet.</p>
          ) : (
            <div className="list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(0,0,0,0.05)',
                    background: 'white',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                    <div style={{ fontWeight: 600, fontSize: '13px' }}>{finding.title}</div>
                    <span className="tag" style={{ fontSize: '11px' }}>{finding.severity}</span>
                  </div>
                  <div className="subtle" style={{ fontSize: '12px', marginTop: '6px' }}>
                    {finding.type}{finding.category ? ` • ${finding.category}` : ''}
                  </div>
                  {finding.confidence_score !== null && finding.confidence_score !== undefined && (
                    <div className="subtle" style={{ fontSize: '11px', marginTop: '6px' }}>
                      Confidence: {finding.confidence_score}%
                    </div>
                  )}
                  <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="subtle" style={{ fontSize: '11px' }}>Status</span>
                    <select
                      className="select"
                      value={finding.status || 'open'}
                      disabled={findingStatusPendingId === String(finding.id)}
                      onChange={(event) => handleFindingStatusChange(finding, event.target.value)}
                      style={{ minHeight: '32px', padding: '6px 8px', fontSize: '12px' }}
                    >
                      {findingStatusOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius-md)', padding: '24px', border: '1px solid rgba(0,0,0,0.05)' }}>
          <h4 style={{ margin: '0 0 16px' }}>Session Settings</h4>

          <div className="field">
            <label className="label" style={{ fontSize: '12px' }}>Session name</label>
            <input
              className="input"
              value={sessionNameDraft}
              onChange={(e) => setSessionNameDraft(e.target.value)}
              onBlur={handleSessionNameSave}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSessionNameSave();
                }
              }}
              placeholder="Name this session"
              disabled={!selectedSessionId}
            />
          </div>

          <div className="field">
            <label className="label" style={{ fontSize: '12px' }}>Project Branch</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <select
                className="select"
                value={selectedBranch}
                onChange={(e) => handleBranchSelect(e.target.value)}
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
                onClick={() => handleBranchSelect(selectedBranch)}
                title="Use selected branch commit"
              >
                +
              </button>
            </div>
            {selectedSession && (
              <p className="subtle" style={{ fontSize: '11px', margin: '8px 0 0' }}>
                Reviewing {selectedSession.branch_name || 'commit'}@{shortSha(selectedSession.commit_sha)}
              </p>
            )}
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
                  {resolveSessionLabel(s)}
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
                <div style={{ fontWeight: 600, fontSize: '14px' }}>{resolveSessionLabel(session)}</div>
                <div className="subtle" style={{ fontSize: '11px' }}>{new Date(session.created_at).toLocaleTimeString()}</div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
