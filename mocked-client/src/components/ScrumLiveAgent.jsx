import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { normalizeList } from '../api/client';

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
    const wsUrl = `ws://localhost:8000/ws/scrum-live/${projectId}/${sessionPart}${token ? `?token=${token}` : ''}`;
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
    <div style={{ display: 'flex', gap: '20px', maxWidth: '1400px', margin: '0 auto', height: 'calc(100vh - 120px)', padding: '20px' }}>
      
      {/* Session Sidebar */}
      <div style={{ width: '280px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div style={{ padding: '15px', background: 'white', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#666', marginBottom: '8px' }}>PROJECT</label>
          <select 
            value={projectId} 
            onChange={(e) => setProjectId(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #ddd' }}
          >
            {projects.map(p => <option key={p.id} value={p.id}>{p.github_full_name || p.name}</option>)}
          </select>
          <button 
            onClick={createNewSession}
            style={{ width: '100%', marginTop: '12px', padding: '10px', background: 'var(--accent-600, #2196F3)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
          >
            + New Session
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', background: 'white', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', padding: '10px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#666', padding: '5px 10px' }}>PAST SESSIONS</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px' }}>
            {sessions.map(s => (
              <div 
                key={s.id} 
                onClick={() => loadSession(s.id)}
                style={{ 
                  padding: '10px', 
                  borderRadius: '8px', 
                  cursor: 'pointer',
                  background: currentSessionId === s.id ? '#e3f2fd' : 'transparent',
                  border: currentSessionId === s.id ? '1px solid #2196F3' : '1px solid transparent',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 600 }}>Session #{s.id}</div>
                <div style={{ fontSize: '11px', color: '#888' }}>{new Date(s.created_at).toLocaleString()}</div>
                <div style={{ fontSize: '11px', color: '#666' }}>{s.message_count} messages</div>
              </div>
            ))}
            {sessions.length === 0 && <div style={{ textAlign: 'center', padding: '20px', color: '#999', fontSize: '13px' }}>No sessions yet</div>}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '20px', borderRadius: '12px', background: 'white', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0 }}>Scrum Live Agent {currentSessionId && <span style={{ color: '#888', fontSize: '16px', fontWeight: 400 }}>— Session #{currentSessionId}</span>}</h2>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            {!connected ? (
              <button 
                onClick={connect} 
                disabled={loading}
                style={{ padding: '10px 20px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
              >
                {loading ? 'Loading...' : 'Connect to Agent'}
              </button>
            ) : (
              <>
                <button onClick={startRecording} style={{ padding: '10px 20px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                  🎤 Start Mic
                </button>
                <button onClick={stopRecording} style={{ padding: '10px 20px', background: '#9e9e9e', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                  ⏹️ Stop Mic
                </button>
                <button onClick={disconnect} style={{ padding: '10px 20px', background: '#f44336', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                  Disconnect
                </button>
              </>
            )}
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: '12px', padding: '20px', marginBottom: '20px', background: '#fcfcfc', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {transcripts.map((t, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: t.source === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px', marginLeft: t.source === 'user' ? 0 : '8px', marginRight: t.source === 'user' ? '8px' : 0 }}>
                {t.source === 'user' ? 'YOU' : 'GEMINI'}
              </div>
              <div style={{ 
                maxWidth: '80%', 
                padding: '12px 16px', 
                borderRadius: '16px', 
                background: t.source === 'user' ? '#2196F3' : '#f0f0f0', 
                color: t.source === 'user' ? 'white' : '#333',
                borderBottomRightRadius: t.source === 'user' ? '4px' : '16px',
                borderBottomLeftRadius: t.source === 'user' ? '16px' : '4px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                lineHeight: 1.5
              }}>
                {t.text}
              </div>
            </div>
          ))}
          
          {transcripts.length === 0 && (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc', flexDirection: 'column', gap: '10px' }}>
               <div style={{ fontSize: '48px' }}>🎙️</div>
               <div>Select a session and connect to start the conversation</div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            value={inputText} 
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendText()}
            placeholder="Type your message to Scrum Master..."
            style={{ flex: 1, padding: '12px 20px', borderRadius: '10px', border: '1px solid #ddd', outline: 'none', fontSize: '15px' }}
          />
          <button 
            onClick={sendText} 
            style={{ padding: '0 25px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}
          >
            Send
          </button>
        </div>
      </div>

      {/* JSON Log Sidebar (Optional/Debug) */}
      <div style={{ width: '350px', padding: '20px', borderRadius: '12px', background: '#1e1e1e', color: '#eee', display: 'flex', flexDirection: 'column' }}>
        <h4 style={{ marginTop: 0, color: '#888', textTransform: 'uppercase', fontSize: '12px', letterSpacing: '1px' }}>Multimodal Live API Streams</h4>
        <div style={{ flex: 1, overflowY: 'auto', fontSize: '11px', fontFamily: '"Fira Code", monospace' }}>
          {jsonLogs.map((log, i) => (
            <div key={i} style={{ 
              marginBottom: '12px', 
              padding: '10px', 
              background: '#2d2d2d', 
              borderRadius: '6px', 
              borderLeft: `3px solid ${log.direction === 'sent' ? '#2196F3' : '#4CAF50'}` 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', color: '#888' }}>
                <span style={{ fontWeight: 600 }}>{log.direction.toUpperCase()}</span>
                <span>{log.timestamp}</span>
              </div>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: '#ccc' }}>
                {JSON.stringify(log.data, null, 2)}
              </pre>
            </div>
          ))}
          {jsonLogs.length === 0 && <div style={{ color: '#555', textAlign: 'center', marginTop: '40px' }}>Waiting for stream data...</div>}
        </div>
      </div>
    </div>
  );
};

export default ScrumLiveAgent;
