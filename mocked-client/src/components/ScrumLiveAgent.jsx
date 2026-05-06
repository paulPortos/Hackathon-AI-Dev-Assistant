import React, { useState, useEffect, useRef } from 'react';

const ScrumLiveAgent = () => {
  const [connected, setConnected] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [inputText, setInputText] = useState('');
  const [jsonLogs, setJsonLogs] = useState([]);
  const ws = useRef(null);
  const playbackAudioContext = useRef(null);
  const microphoneAudioContext = useRef(null);
  const microphone = useRef(null);
  const workletNode = useRef(null);
  const nextStartTime = useRef(0);

  const activeSources = useRef([]);
  const turnBuffer = useRef({ text: '', audioChunks: 0 });


  const addJsonLog = (direction, data) => {
    // Deep clone to avoid mutating the original message
    const cleanData = JSON.parse(JSON.stringify(data));
    
    // Recursive function to mask audio data
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
        // Group consecutive sent audio chunks (Mic input)
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
    nextStartTime.current = 0;
    ws.current = new WebSocket('ws://localhost:8000/ws/scrum-live/');

    
    ws.current.onopen = () => {
      setConnected(true);
      console.log('Connected to Scrum Live Server');
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
      try {
        source.stop();
      } catch (e) {
        // Source might have already stopped
      }
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

      // Load AudioWorklet
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
    if (workletNode.current) {
      workletNode.current.disconnect();
      workletNode.current = null;
    }
    if (microphone.current) {
      microphone.current.disconnect();
      microphone.current = null;
    }
    if (microphoneAudioContext.current) {
      microphoneAudioContext.current.close();
      microphoneAudioContext.current = null;
    }
    nextStartTime.current = 0;
    console.log('Recording stopped');

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
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    const pcmData = new Int16Array(bytes.buffer);
    const float32Data = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      float32Data[i] = pcmData[i] / 0x8000;
    }

    const buffer = playbackAudioContext.current.createBuffer(1, float32Data.length, 24000);
    buffer.getChannelData(0).set(float32Data);
    
    const source = playbackAudioContext.current.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackAudioContext.current.destination);
    
    activeSources.current.push(source);
    source.onended = () => {
      activeSources.current = activeSources.current.filter(s => s !== source);
    };
    
    // Scheduling to prevent overlap
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
    <div style={{ display: 'flex', gap: '20px', maxWidth: '1200px', margin: '20px auto', height: 'calc(100vh - 150px)' }}>
      {/* Main Content */}
      <div style={{ flex: 1, padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: 'white', display: 'flex', flexDirection: 'column' }}>
        <h2>Scrum Live Agent</h2>
        
        <div style={{ marginBottom: '20px' }}>
          {!connected ? (
            <button onClick={connect} style={{ padding: '10px 20px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
              Connect to Agent
            </button>
          ) : (
            <div>
              <button onClick={disconnect} style={{ padding: '10px 20px', background: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px' }}>
                Disconnect
              </button>
              <button onClick={startRecording} style={{ padding: '10px 20px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px' }}>
                Start Mic
              </button>
              <button onClick={stopRecording} style={{ padding: '10px 20px', background: '#9e9e9e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                Stop Mic
              </button>
            </div>
          )}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #eee', padding: '10px', marginBottom: '20px', background: '#fafafa' }}>
          {transcripts.map((t, i) => (
            <div key={i} style={{ marginBottom: '10px', textAlign: t.source === 'user' ? 'right' : 'left' }}>
              <span style={{ fontWeight: 'bold', color: t.source === 'user' ? '#2196F3' : '#FF5722' }}>
                {t.source === 'user' ? 'You' : 'Gemini'}:
              </span>
              <p style={{ margin: '5px 0', background: t.source === 'user' ? '#e3f2fd' : '#fff3e0', padding: '8px', borderRadius: '8px', display: 'inline-block' }}>
                {t.text}
              </p>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex' }}>
          <input 
            type="text" 
            value={inputText} 
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendText()}
            placeholder="Type a message..."
            style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc', marginRight: '10px' }}
          />
          <button onClick={sendText} style={{ padding: '10px 20px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Send
          </button>
        </div>
      </div>

      {/* JSON Log Sidebar */}
      <div style={{ width: '400px', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: '#f5f5f5', display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ marginTop: 0 }}>Live API Logs</h3>
        <div style={{ flex: 1, overflowY: 'auto', fontSize: '12px', fontFamily: 'monospace' }}>
          {jsonLogs.map((log, i) => (
            <div key={i} style={{ 
              marginBottom: '10px', 
              padding: '8px', 
              background: 'white', 
              borderRadius: '4px', 
              borderLeft: `4px solid ${log.direction === 'sent' ? '#2196F3' : '#4CAF50'}` 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', color: '#666' }}>
                <span>{log.direction.toUpperCase()}</span>
                <span>{log.timestamp}</span>
              </div>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {JSON.stringify(log.data, null, 2)}
              </pre>
            </div>
          ))}
          {jsonLogs.length === 0 && <div style={{ color: '#999', textAlign: 'center', marginTop: '20px' }}>No messages yet...</div>}
        </div>
      </div>
    </div>
  );
};

export default ScrumLiveAgent;
