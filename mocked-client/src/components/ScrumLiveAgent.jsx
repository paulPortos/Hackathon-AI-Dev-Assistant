import React, { useState, useEffect, useRef } from 'react';

const ScrumLiveAgent = () => {
  const [connected, setConnected] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [inputText, setInputText] = useState('');
  const ws = useRef(null);
  const audioContext = useRef(null);
  const microphone = useRef(null);
  const workletNode = useRef(null);
  const nextStartTime = useRef(0);

  const activeSources = useRef([]);


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
        setTranscripts(prev => {
          if (prev.length > 0 && prev[prev.length - 1].source === message.source) {
            // Append to last message if same source
            const last = prev[prev.length - 1];
            return [...prev.slice(0, -1), { ...last, text: last.text + (last.text.endsWith(' ') ? '' : ' ') + message.text }];
          }
          return [...prev, { source: message.source, text: message.text }];
        });
      } else if (message.type === 'audio') {
        playAudio(message.data);
      } else if (message.type === 'interrupted') {
        console.log('Agent interrupted');
        stopAudio();
      } else if (message.type === 'turn_complete') {
        console.log('Agent turn complete');
      } else if (message.type === 'error') {
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
      audioContext.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      microphone.current = audioContext.current.createMediaStreamSource(stream);

      // Load AudioWorklet
      await audioContext.current.audioWorklet.addModule('/src/components/AudioWorkletProcessor.js');
      workletNode.current = new AudioWorkletNode(audioContext.current, 'audio-worklet-processor');

      workletNode.current.port.onmessage = (event) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          const pcmBuffer = event.data;
          const base64Audio = btoa(String.fromCharCode(...new Uint8Array(pcmBuffer)));
          ws.current.send(JSON.stringify({ type: 'audio', data: base64Audio }));
        }
      };

      microphone.current.connect(workletNode.current);
      workletNode.current.connect(audioContext.current.destination);
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
    if (audioContext.current) {
      audioContext.current.close();
      audioContext.current = null;
    }
    nextStartTime.current = 0;
    console.log('Recording stopped');

  };

  const playAudio = (base64Data) => {
    if (!audioContext.current) {
        audioContext.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    }
    
    if (audioContext.current.state === 'suspended') {
        audioContext.current.resume();
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

    const buffer = audioContext.current.createBuffer(1, float32Data.length, 24000);
    buffer.getChannelData(0).set(float32Data);
    
    const source = audioContext.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.current.destination);
    
    activeSources.current.push(source);
    source.onended = () => {
      activeSources.current = activeSources.current.filter(s => s !== source);
    };
    
    // Scheduling to prevent overlap
    const startTime = Math.max(audioContext.current.currentTime, nextStartTime.current);
    source.start(startTime);
    nextStartTime.current = startTime + buffer.duration;
  };


  const sendText = () => {
    if (ws.current && inputText.trim()) {
      ws.current.send(JSON.stringify({ type: 'text', text: inputText }));
      setTranscripts(prev => [...prev, { source: 'user', text: inputText }]);
      setInputText('');
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', maxWidth: '600px', margin: '20px auto' }}>
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

      <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #eee', padding: '10px', marginBottom: '20px', background: '#fafafa' }}>
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
  );
};

export default ScrumLiveAgent;
