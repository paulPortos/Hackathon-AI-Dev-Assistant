import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { normalizeList } from '../api/client';
import { WS_ROOT } from '../api/config';

const ScrumLiveAgent = () => {
  const [searchParams] = useSearchParams();
  const [projectId, setProjectId] = useState(searchParams.get('projectId') || '');
  const [projects, setProjects] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  
  const [connected, setConnected] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [inputText, setInputText] = useState('');
  const [jsonLogs, setJsonLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // UI States
  const [leftSidebarVisible, setLeftSidebarVisible] = useState(true);
  const [rightSidebarVisible, setRightSidebarVisible] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900);

  // Handle window resize for responsiveness
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 900;
      setIsMobile(mobile);
      if (mobile) {
        setLeftSidebarVisible(false);
        setRightSidebarVisible(false);
      } else {
        setLeftSidebarVisible(true);
        setRightSidebarVisible(true);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const ws = useRef(null);
  const playbackAudioContext = useRef(null);
  const microphoneAudioContext = useRef(null);
  const microphone = useRef(null);
  const workletNode = useRef(null);
  const nextStartTime = useRef(0);

  const activeSources = useRef([]);
  const turnBuffer = useRef({ text: '', audioChunks: 0 });

  // Fetch initial data
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const payload = await api.listProjects();
        const normalized = normalizeList(payload);
        setProjects(normalized);
        if (!projectId && normalized.length > 0) {
          setProjectId(normalized[0].id);
        }
      } catch (err) {
        console.error('Error fetching projects:', err);
      }
    };
    fetchProjects();
  }, []);

  // Fetch sessions when projectId changes
  useEffect(() => {
    if (projectId) {
      fetchSessions();
    }
  }, [projectId]);

  const fetchSessions = async () => {
    try {
      const payload = await api.listScrumSessions(projectId);
      setSessions(normalizeList(payload));
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

  const loadSession = async (sessionId) => {
    setLoading(true);
    disconnect();
    setCurrentSessionId(sessionId);
    setTranscripts([]);
    setJsonLogs([]);
    
    try {
      const messages = await api.listScrumMessages(sessionId);
      const formattedMessages = messages.map(m => ({
        source: m.role === 'user' ? 'user' : 'gemini',
        text: m.text_content
      }));
      setTranscripts(formattedMessages);
    } catch (err) {
      console.error('Error loading session history:', err);
    } finally {
      setLoading(false);
    }
  };

  const createNewSession = async () => {
    if (!projectId) return;
    try {
      const session = await api.createScrumSession({ project: projectId });
      setSessions(prev => [session, ...prev]);
      loadSession(session.id);
    } catch (err) {
      console.error('Error creating session:', err);
    }
  };

  const deleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this session?")) return;
    
    try {
      await api.deleteScrumSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setTranscripts([]);
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      alert('Failed to delete session');
    }
  };

  const addJsonLog = (direction, data) => {
    const cleanData = JSON.parse(JSON.stringify(data));
    const maskAudio = (obj) => {
      if (!obj || typeof obj !== 'object') return;
      if (obj.data && typeof obj.data === 'string' && obj.data.length > 100) {
        obj.data = '[audio]';
      }
      if (obj.inline_data && obj.inline_data.data) {
        obj.inline_data.data = '[audio]';
      }
      Object.values(obj).forEach(val => maskAudio(val));
    };
    maskAudio(cleanData);
    
    setJsonLogs(prev => {
      if (prev.length > 0) {
        const last = prev[0];
        if (direction === 'sent' && last.direction === 'sent' && cleanData.type === 'audio') {
          const count = (last.count || 1) + 1;
          return [
            { ...last, timestamp: new Date().toLocaleTimeString(), count, data: { type: 'audio', status: `Mic streaming... (${count} chunks)` } },
            ...prev.slice(1)
          ];
        }
      }
      return [
        { direction, timestamp: new Date().toLocaleTimeString(), data: cleanData },
        ...prev
      ].slice(0, 50);
    });
  };

  const connect = () => {
    if (!projectId) return alert("Please select a project first");
    
    nextStartTime.current = 0;
    const sessionPart = currentSessionId ? `${currentSessionId}/` : '';
    const token = localStorage.getItem('mocked-client.access-token');
    const wsUrl = `${WS_ROOT}/scrum-live/${projectId}/${sessionPart}${token ? `?token=${token}` : ''}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setConnected(true);
      console.log('Connected to Scrum Live Server');
      // If we didn't have a session ID before, the server created one.
      // We'll need a way to know which one it is if we want to sync the UI.
      // For now, let's just refresh the session list.
      fetchSessions();
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'transcription') {
        turnBuffer.current.text += message.text;
        setTranscripts(prev => {
          if (prev.length > 0 && prev[prev.length - 1].source === message.source) {
            const last = prev[prev.length - 1];
            return [...prev.slice(0, -1), { ...last, text: last.text + (last.text.endsWith(' ') ? '' : ' ') + message.text }];
          }
          return [...prev, { source: message.source, text: message.text }];
        });
      } else if (message.type === 'audio') {
        turnBuffer.current.audioChunks++;
        playAudio(message.data);
      } else if (message.type === 'interrupted') {
        addJsonLog('received', { type: 'interrupted', partial_text: turnBuffer.current.text });
        turnBuffer.current = { text: '', audioChunks: 0 };
        stopAudio();
      } else if (message.type === 'turn_complete') {
        addJsonLog('received', { 
          type: 'turn_complete', 
          final_text: turnBuffer.current.text.trim(),
          audio_chunks: turnBuffer.current.audioChunks 
        });
        turnBuffer.current = { text: '', audioChunks: 0 };
      } else if (message.type === 'error') {
        addJsonLog('received', message);
        console.error('Gemini Error:', message.message);
      } else if (message.type === 'kanban_update') {
        addJsonLog('received', { type: 'kanban_update', message: 'Kanban board modified by agent' });
      }
    };

    ws.current.onclose = () => {
      setConnected(false);
      stopRecording();
      stopAudio();
      console.log('Disconnected from Scrum Live Server');
    };
  };

  const stopAudio = () => {
    activeSources.current.forEach(source => {
      try { source.stop(); } catch (e) {}
    });
    activeSources.current = [];
    nextStartTime.current = 0;
  };

  const disconnect = () => {
    if (ws.current) ws.current.close();
  };

  const startRecording = async () => {
    stopAudio();
    try {
      microphoneAudioContext.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      microphone.current = microphoneAudioContext.current.createMediaStreamSource(stream);

      await microphoneAudioContext.current.audioWorklet.addModule('/src/components/AudioWorkletProcessor.js');
      workletNode.current = new AudioWorkletNode(microphoneAudioContext.current, 'audio-worklet-processor');

      workletNode.current.port.onmessage = (event) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          const pcmBuffer = event.data;
          const base64Audio = btoa(String.fromCharCode(...new Uint8Array(pcmBuffer)));
          const msg = { type: 'audio', data: base64Audio };
          ws.current.send(JSON.stringify(msg));
          addJsonLog('sent', msg); 
        }
      };

      microphone.current.connect(workletNode.current);
      workletNode.current.connect(microphoneAudioContext.current.destination);
      console.log('Recording started');
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (workletNode.current) { workletNode.current.disconnect(); workletNode.current = null; }
    if (microphone.current) { microphone.current.disconnect(); microphone.current = null; }
    if (microphoneAudioContext.current) { microphoneAudioContext.current.close(); microphoneAudioContext.current = null; }
    nextStartTime.current = 0;
  };

  const playAudio = (base64Data) => {
    if (!playbackAudioContext.current) {
        playbackAudioContext.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    }
    if (playbackAudioContext.current.state === 'suspended') {
        playbackAudioContext.current.resume();
    }
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
    
    const pcmData = new Int16Array(bytes.buffer);
    const float32Data = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) float32Data[i] = pcmData[i] / 0x8000;

    const buffer = playbackAudioContext.current.createBuffer(1, float32Data.length, 24000);
    buffer.getChannelData(0).set(float32Data);
    
    const source = playbackAudioContext.current.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackAudioContext.current.destination);
    activeSources.current.push(source);
    source.onended = () => { activeSources.current = activeSources.current.filter(s => s !== source); };
    
    const startTime = Math.max(playbackAudioContext.current.currentTime, nextStartTime.current);
    source.start(startTime);
    nextStartTime.current = startTime + buffer.duration;
  };

  const sendText = () => {
    if (ws.current && inputText.trim()) {
      const msg = { type: 'text', text: inputText };
      ws.current.send(JSON.stringify(msg));
      addJsonLog('sent', msg);
      setTranscripts(prev => [...prev, { source: 'user', text: inputText }]);
      setInputText('');
    }
  };


  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      gap: isMobile ? '10px' : '20px', 
      maxWidth: '1600px', 
      margin: '0 auto', 
      height: isMobile ? 'auto' : 'calc(100vh - 120px)', 
      minHeight: isMobile ? 'calc(100vh - 100px)' : 'unset',
      padding: isMobile ? '10px' : '20px',
      position: 'relative'
    }}>
      
      {/* Top Toolbar for Sidebar Toggles */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '10px 20px',
        background: 'rgba(255, 255, 255, 0.7)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
        border: '1px solid rgba(135, 120, 89, 0.1)',
        marginBottom: '10px'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            onClick={() => setLeftSidebarVisible(!leftSidebarVisible)}
            style={{ 
              background: leftSidebarVisible ? 'var(--sage-700, #4b5a3a)' : 'white', 
              color: leftSidebarVisible ? 'white' : 'var(--ink-700, #3b4237)',
              border: '1px solid rgba(0,0,0,0.1)', 
              borderRadius: '12px', 
              padding: '8px 16px', 
              fontSize: '13px', 
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: leftSidebarVisible ? '0 4px 12px rgba(75, 90, 58, 0.3)' : '0 2px 4px rgba(0,0,0,0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {leftSidebarVisible ? 'Hide Sessions ◀' : 'Show Sessions ▶'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            onClick={() => setRightSidebarVisible(!rightSidebarVisible)}
            style={{ 
              background: rightSidebarVisible ? 'var(--accent-500, #c57b3f)' : 'white', 
              color: rightSidebarVisible ? 'white' : 'var(--ink-700, #3b4237)',
              border: '1px solid rgba(0,0,0,0.1)', 
              borderRadius: '12px', 
              padding: '8px 16px', 
              fontSize: '13px', 
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: rightSidebarVisible ? '0 4px 12px rgba(197, 123, 63, 0.3)' : '0 2px 4px rgba(0,0,0,0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {rightSidebarVisible ? 'Hide Console ▶' : '◀ Show Console'}
          </button>
        </div>
      </div>

      <div style={{ 
        display: 'flex', 
        flex: 1, 
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? '15px' : '20px', 
        padding: '5px',
        overflow: isMobile ? 'visible' : 'hidden' // Allow scrolling on mobile if sidebars are stacked
      }}>
        {/* Session Sidebar */}
        <div style={{ 
          width: isMobile ? '100%' : (leftSidebarVisible ? '300px' : '0px'), 
          opacity: leftSidebarVisible ? 1 : 0,
          display: leftSidebarVisible ? 'flex' : 'none',
          flexDirection: 'column', 
          gap: '15px', 
          transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          flexShrink: 0
        }}>
          <div style={{ padding: '20px', background: 'white', borderRadius: '20px', boxShadow: '0 8px 30px rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.02)' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#999', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Project Context</label>
            <select 
              value={projectId} 
              onChange={(e) => setProjectId(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #eee', background: '#fcfcfc', fontSize: '14px', outline: 'none' }}
            >
              {projects.map(p => <option key={p.id} value={p.id}>{p.github_full_name || p.name}</option>)}
            </select>
            <button 
              onClick={createNewSession}
              style={{ width: '100%', marginTop: '15px', padding: '12px', background: 'var(--accent-500, #c57b3f)', color: 'white', border: 'none', borderRadius: '12px', cursor: 'pointer', fontWeight: 700, boxShadow: '0 10px 20px rgba(197, 123, 63, 0.2)', transition: 'all 0.2s' }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              + New Session
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', background: 'white', borderRadius: '20px', boxShadow: '0 8px 30px rgba(0,0,0,0.04)', padding: '15px', border: '1px solid rgba(0,0,0,0.02)' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#999', padding: '5px 10px', textTransform: 'uppercase' }}>History</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
              {sessions.map(s => (
                <div 
                  key={s.id} 
                  onClick={() => loadSession(s.id)}
                  style={{ 
                    padding: '12px 15px', 
                    borderRadius: '14px', 
                    cursor: 'pointer',
                    background: currentSessionId === s.id ? 'var(--khaki-50, #f8f4ea)' : 'transparent',
                    border: currentSessionId === s.id ? '1px solid var(--accent-300, #e4b47f)' : '1px solid transparent',
                    transition: 'all 0.2s ease',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ overflow: 'hidden' }}>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: currentSessionId === s.id ? 'var(--ink-900)' : 'var(--ink-700)' }}>Session #{s.id}</div>
                      <div style={{ fontSize: '11px', color: '#aaa', marginTop: '2px' }}>{new Date(s.created_at).toLocaleDateString()} at {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                    <button 
                      onClick={(e) => deleteSession(e, s.id)}
                      style={{ 
                        background: 'rgba(255, 82, 82, 0.1)', 
                        border: 'none', 
                        color: '#ff5252', 
                        cursor: 'pointer',
                        padding: '6px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 82, 82, 0.2)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255, 82, 82, 0.1)'}
                      title="Delete Session"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
              {sessions.length === 0 && <div style={{ textAlign: 'center', padding: '40px 20px', color: '#ccc', fontSize: '13px' }}>No sessions found</div>}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div style={{ 
          flex: 1, 
          padding: isMobile ? '15px' : '25px', 
          borderRadius: '24px', 
          background: 'white', 
          boxShadow: '0 10px 40px rgba(0,0,0,0.06)', 
          border: '1px solid rgba(0,0,0,0.02)', 
          display: 'flex', 
          flexDirection: 'column',
          minHeight: isMobile ? '450px' : 'unset',
          maxHeight: isMobile ? 'calc(100vh - 200px)' : 'unset' // Better constraint for mobile viewport
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', marginBottom: '25px', flexDirection: isMobile ? 'column' : 'row', gap: '15px' }}>
            <h2 style={{ margin: 0, fontFamily: 'Fraunces, serif', fontSize: isMobile ? '20px' : '24px' }}>Scrum Live Master {currentSessionId && <span style={{ color: 'var(--ink-500)', fontSize: isMobile ? '14px' : '16px', fontWeight: 400, marginLeft: isMobile ? '0' : '12px', display: isMobile ? 'block' : 'inline' }}>— Session #{currentSessionId}</span>}</h2>
            
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {!connected ? (
                <button 
                  onClick={connect} 
                  disabled={loading}
                  style={{ padding: '12px 24px', background: 'var(--sage-700, #4b5a3a)', color: 'white', border: 'none', borderRadius: '14px', cursor: 'pointer', fontWeight: 600, boxShadow: '0 8px 20px rgba(75, 90, 58, 0.2)' }}
                >
                  {loading ? 'Preparing...' : 'Connect to Agent'}
                </button>
              ) : (
                <>
                  <button onClick={startRecording} style={{ padding: '12px 24px', background: 'var(--accent-500, #c57b3f)', color: 'white', border: 'none', borderRadius: '14px', cursor: 'pointer', fontWeight: 600, boxShadow: '0 8px 20px rgba(197, 123, 63, 0.2)' }}>
                    🎤 Start Mic
                  </button>
                  <button onClick={stopRecording} style={{ padding: '12px 24px', background: '#f0f0f0', color: 'var(--ink-700)', border: 'none', borderRadius: '14px', cursor: 'pointer', fontWeight: 600 }}>
                    ⏹️ Stop
                  </button>
                  <button onClick={disconnect} style={{ padding: '12px 24px', background: 'rgba(255, 82, 82, 0.1)', color: '#ff5252', border: 'none', borderRadius: '14px', cursor: 'pointer', fontWeight: 600 }}>
                    Disconnect
                  </button>
                </>
              )}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #f8f8f8', borderRadius: '20px', padding: '25px', marginBottom: '25px', background: '#fafafa', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {transcripts.map((t, i) => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: t.source === 'user' ? 'flex-end' : 'flex-start', animation: 'fadeIn 0.3s ease-out' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-500)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '1px', marginLeft: t.source === 'user' ? 0 : '12px', marginRight: t.source === 'user' ? '12px' : 0 }}>
                  {t.source === 'user' ? 'Collaborator' : 'Scrum Master'}
                </div>
                <div style={{ 
                  maxWidth: '75%', 
                  padding: '16px 20px', 
                  borderRadius: '20px', 
                  background: t.source === 'user' ? 'var(--accent-500, #c57b3f)' : 'white', 
                  color: t.source === 'user' ? 'white' : 'var(--ink-900)',
                  borderTopRightRadius: t.source === 'user' ? '4px' : '20px',
                  borderTopLeftRadius: t.source === 'user' ? '20px' : '4px',
                  boxShadow: '0 4px 15px rgba(0,0,0,0.04)',
                  border: t.source === 'user' ? 'none' : '1px solid #eee',
                  lineHeight: 1.6,
                  fontSize: '15px'
                }}>
                  {t.text}
                </div>
              </div>
            ))}
            
            {transcripts.length === 0 && (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ddd', flexDirection: 'column', gap: '15px' }}>
                 <div style={{ fontSize: '64px', opacity: 0.5 }}>🎙️</div>
                 <div style={{ fontSize: '16px', fontWeight: 500 }}>Connection established. Waiting for your input.</div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <input 
              type="text" 
              value={inputText} 
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendText()}
              placeholder="Collaborate with your AI Scrum Master..."
              style={{ flex: 1, padding: '18px 25px', borderRadius: '18px', border: '1px solid #eee', outline: 'none', fontSize: '16px', background: '#fdfdfd', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)' }}
            />
            <button 
              onClick={sendText} 
              style={{ padding: '0 35px', background: 'var(--sage-700, #4b5a3a)', color: 'white', border: 'none', borderRadius: '18px', cursor: 'pointer', fontWeight: 700, boxShadow: '0 8px 20px rgba(75, 90, 58, 0.2)', transition: 'all 0.2s' }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Send
            </button>
          </div>
        </div>

        {/* JSON Log Sidebar */}
        <div style={{ 
          width: isMobile ? '100%' : (rightSidebarVisible ? '360px' : '0px'), 
          opacity: rightSidebarVisible ? 1 : 0,
          display: rightSidebarVisible ? 'flex' : 'none',
          padding: rightSidebarVisible ? (isMobile ? '20px' : '25px') : '0px', 
          borderRadius: '24px', 
          background: 'white', 
          color: 'var(--ink-900, #1f241d)', 
          flexDirection: 'column',
          transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          flexShrink: 0,
          boxShadow: '0 10px 40px rgba(0,0,0,0.06)',
          border: '1px solid rgba(0,0,0,0.02)',
          marginTop: isMobile ? '10px' : '0px'
        }}>
          <h4 style={{ marginTop: 0, color: 'var(--accent-500, #c57b3f)', textTransform: 'uppercase', fontSize: '12px', letterSpacing: '2px', fontWeight: 800, marginBottom: '20px' }}>Multimodal Streams</h4>
          
          <div style={{ flex: 1, overflowY: 'auto', fontSize: '12px', fontFamily: '"Space Mono", monospace', paddingRight: '5px' }}>
            {jsonLogs.map((log, i) => (
              <div key={i} style={{ 
                marginBottom: '15px', 
                padding: '12px', 
                background: 'var(--khaki-50, #f8f4ea)', 
                borderRadius: '12px', 
                borderLeft: `4px solid ${log.direction === 'sent' ? 'var(--accent-500)' : 'var(--sage-700)'}`,
                border: '1px solid rgba(135, 120, 89, 0.1)',
                overflow: 'hidden'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--ink-500)', fontSize: '10px', fontWeight: 700 }}>
                  <span style={{ color: log.direction === 'sent' ? 'var(--accent-500)' : 'var(--sage-600)' }}>{log.direction.toUpperCase()}</span>
                  <span>{log.timestamp}</span>
                </div>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'var(--ink-700)', lineHeight: 1.4 }}>
                  {JSON.stringify(log.data, null, 2)}
                </pre>
              </div>
            ))}
            {jsonLogs.length === 0 && <div style={{ color: 'var(--ink-500)', textAlign: 'center', marginTop: '60px', fontStyle: 'italic' }}>Live stream data will appear here...</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScrumLiveAgent;
