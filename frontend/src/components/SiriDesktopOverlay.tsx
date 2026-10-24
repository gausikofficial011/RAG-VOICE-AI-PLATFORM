import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { siriSounds } from '../services/siriSounds';
import { VoiceOrb, type VoiceState } from './VoiceOrb';
import {
  Sparkles,
  X,
  Radio,
  Volume2,
  Mic,
  Cpu,
  HardDrive,
  Activity,
  Battery,
  Search,
  Trash2,
  FileCheck,
  CheckCircle2,
  Terminal,
} from 'lucide-react';
import type { KnowledgeBase } from '../types';

interface SiriDesktopOverlayProps {
  knowledgeBases: KnowledgeBase[];
  selectedKBId: string | null;
  onOpenPortal?: (portal: any) => void;
}

export const SiriDesktopOverlay: React.FC<SiriDesktopOverlayProps> = ({
  knowledgeBases,
  selectedKBId,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [latestAnswer, setLatestAnswer] = useState('');
  const [latestAudio, setLatestAudio] = useState<string | null>(null);
  const [citations, setCitations] = useState<any[]>([]);
  const [telemetry, setTelemetry] = useState<any | null>(null);
  const [executedTools, setExecutedTools] = useState<any[]>([]);
  const [agentActionType, setAgentActionType] = useState<string | null>(null);
  const [isHeySiriListening, setIsHeySiriListening] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const effectiveKBId = selectedKBId || (knowledgeBases.length > 0 ? knowledgeBases[0].id : undefined);

  // Audio recording & Speech recognition refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const activeRecognitionRef = useRef<any>(null);
  const passiveWakeWordRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);

  // Load telemetry when Siri opens
  useEffect(() => {
    if (isOpen) {
      loadTelemetry();
    }
  }, [isOpen]);

  async function loadTelemetry() {
    try {
      const data = await api.getAgentTelemetry();
      setTelemetry(data);
    } catch {}
  }

  // 1. Setup Global Laptop Shortcut: Alt + S
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Alt + S to toggle Siri anywhere
      if (e.altKey && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        toggleSiriActive();
      }
      // Escape to close Siri
      if (e.key === 'Escape' && isOpen) {
        handleDismissSiri();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, voiceState]);

  // 2. Setup Background Hands-Free "Hey Siri" Wake Word Listener
  useEffect(() => {
    if (!isHeySiriListening || isOpen) {
      stopPassiveWakeWordListener();
      return;
    }

    startPassiveWakeWordListener();

    return () => {
      stopPassiveWakeWordListener();
    };
  }, [isHeySiriListening, isOpen]);

  function startPassiveWakeWordListener() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript.toLowerCase();
        }

        const wakePhrases = ['hey siri', 'siri', 'hey assistant', 'ok siri'];
        const matchedPhrase = wakePhrases.find((p) => currentTranscript.includes(p));

        if (matchedPhrase) {
          console.log('[Siri Engine] Wake Word Detected:', matchedPhrase);
          stopPassiveWakeWordListener();

          const parts = currentTranscript.split(matchedPhrase);
          const trailingQuery = parts[parts.length - 1]?.trim().replace(/^[,. ]+/, '');

          setIsOpen(true);
          setIsMinimized(false);
          siriSounds.playWakeChime();

          if (trailingQuery && trailingQuery.length > 3) {
            setTranscript(trailingQuery);
            handleExecuteSiriTextQuery(trailingQuery);
          } else {
            handleStartActiveListening();
          }
        }
      };

      recognition.onerror = () => {
        if (isHeySiriListening && !isOpen) {
          setTimeout(() => {
            try { recognition.start(); } catch {}
          }, 1000);
        }
      };

      recognition.onend = () => {
        if (isHeySiriListening && !isOpen) {
          setTimeout(() => {
            try { recognition.start(); } catch {}
          }, 500);
        }
      };

      recognition.start();
      passiveWakeWordRef.current = recognition;
    } catch (e) {
      console.warn('Wake-word listener initialization notice:', e);
    }
  }

  function stopPassiveWakeWordListener() {
    if (passiveWakeWordRef.current) {
      try {
        passiveWakeWordRef.current.onend = null;
        passiveWakeWordRef.current.stop();
      } catch {}
      passiveWakeWordRef.current = null;
    }
  }

  function toggleSiriActive() {
    if (isOpen) {
      handleDismissSiri();
    } else {
      setIsOpen(true);
      setIsMinimized(false);
      siriSounds.playWakeChime();
      handleStartActiveListening();
    }
  }

  function handleDismissSiri() {
    stopActiveRecording();
    stopAudio();
    siriSounds.playDismissChime();
    setIsOpen(false);
    setVoiceState('IDLE');
    setTranscript('');
    setExecutedTools([]);
    setAgentActionType(null);
    setErrorMessage(null);
  }

  // 3. Active Siri Speech Recording with Auto-Silence Detection
  async function handleStartActiveListening() {
    stopAudio();
    setVoiceState('LISTENING');
    setTranscript('');
    setLatestAnswer('');
    setExecutedTools([]);
    setAgentActionType(null);
    setErrorMessage(null);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = true;
          rec.interimResults = true;
          rec.lang = 'en-US';

          rec.onresult = (e: any) => {
            let fullText = '';
            for (let i = 0; i < e.results.length; i++) {
              fullText += e.results[i][0].transcript;
            }
            if (fullText) {
              setTranscript(fullText);

              if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
              silenceTimerRef.current = setTimeout(() => {
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                  mediaRecorderRef.current.stop();
                }
              }, 1800);
            }
          };

          rec.start();
          activeRecognitionRef.current = rec;
        } catch (e) {
          console.warn('Active speech recognition notice:', e);
        }
      }

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (activeRecognitionRef.current) {
          try { activeRecognitionRef.current.stop(); } catch {}
          activeRecognitionRef.current = null;
        }
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

        const finalAudioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        submitVoiceQuery(finalAudioBlob);
      };

      mediaRecorder.start();
    } catch (err: any) {
      setErrorMessage(`Microphone access error: ${err.message}`);
      setVoiceState('IDLE');
    }
  }

  function stopActiveRecording() {
    if (activeRecognitionRef.current) {
      try { activeRecognitionRef.current.stop(); } catch {}
      activeRecognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
  }

  // 4. Submit Query to Backend
  async function submitVoiceQuery(audioBlob: Blob) {
    setVoiceState('THINKING');
    try {
      const res = await api.voiceQuery(
        audioBlob,
        effectiveKBId,
        undefined,
        'en',
        transcript.trim() || undefined
      );

      setTranscript(res.transcript || transcript);
      setLatestAnswer(res.answer);
      setCitations(res.citations || []);
      if (res.executed_tools) setExecutedTools(res.executed_tools);
      if (res.action_type) setAgentActionType(res.action_type);

      loadTelemetry();

      if (res.audio_base64) {
        setLatestAudio(res.audio_base64);
        playSiriAudio(res.audio_base64);
      } else {
        setVoiceState('IDLE');
      }
    } catch (err: any) {
      setErrorMessage(`Siri error: ${err.message}`);
      setVoiceState('IDLE');
    }
  }

  async function handleExecuteSiriTextQuery(text: string) {
    setVoiceState('THINKING');
    try {
      const res = await api.queryRAG({
        query: text,
        kb_id: effectiveKBId,
        audio_requested: true,
        language: 'en',
      });

      setLatestAnswer(res.answer);
      setCitations(res.citations || []);
      if (res.executed_tools) setExecutedTools(res.executed_tools);
      if (res.action_type) setAgentActionType(res.action_type);

      loadTelemetry();

      if (res.audio_base64) {
        setLatestAudio(res.audio_base64);
        playSiriAudio(res.audio_base64);
      } else {
        setVoiceState('IDLE');
      }
    } catch (err: any) {
      setErrorMessage(`Siri query error: ${err.message}`);
      setVoiceState('IDLE');
    }
  }

  // Quick One-Click Agent Workflow Runner
  async function handleRunAgentWorkflow(command: string) {
    stopAudio();
    setTranscript(command);
    setVoiceState('THINKING');
    setExecutedTools([]);
    setAgentActionType(null);

    try {
      const res = await api.executeAgentCommand(command, true);
      setLatestAnswer(res.answer);
      if (res.executed_tools) setExecutedTools(res.executed_tools);
      if (res.action_type) setAgentActionType(res.action_type);

      loadTelemetry();

      if (res.audio_base64) {
        setLatestAudio(res.audio_base64);
        playSiriAudio(res.audio_base64);
      } else {
        setVoiceState('IDLE');
      }
    } catch (err: any) {
      setErrorMessage(`Agent error: ${err.message}`);
      setVoiceState('IDLE');
    }
  }

  // 5. Audio Playback
  function playSiriAudio(audioBase64: string) {
    stopAudio();
    try {
      const audio = new Audio(audioBase64);
      currentAudioRef.current = audio;
      setVoiceState('SPEAKING');

      audio.onended = () => {
        setVoiceState('IDLE');
        siriSounds.playSuccessChime();
      };
      audio.onerror = () => {
        setVoiceState('IDLE');
      };
      audio.play().catch((err) => {
        console.warn('Playback notice:', err);
        setVoiceState('IDLE');
      });
    } catch (e) {
      setVoiceState('IDLE');
    }
  }

  function stopAudio() {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
  }

  // If closed, show the floating Apple Siri button in bottom-right corner
  if (!isOpen) {
    return (
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9997,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <button
          onClick={toggleSiriActive}
          style={{
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            border: '1px solid rgba(255, 255, 255, 0.16)',
            borderRadius: '30px',
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5), 0 0 25px rgba(56, 189, 248, 0.25)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          title="Click or press Alt+S or say 'Hey Siri'"
        >
          {/* Mini Glowing Siri Core */}
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'conic-gradient(from 0deg, #06b6d4, #8b5cf6, #ec4899, #f43f5e, #10b981, #06b6d4)',
              boxShadow: '0 0 12px rgba(236, 72, 153, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'spin 6s linear infinite',
            }}
          >
            <Mic size={14} color="#ffffff" />
          </div>

          <div style={{ textAlign: 'left' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc', display: 'block' }}>
              Hey Siri PC Agent
            </span>
            <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
              {isHeySiriListening ? 'Say "Hey Siri" or Alt+S' : 'Click to activate'}
            </span>
          </div>
        </button>
      </div>
    );
  }

  return (
    <>
      {/* Floating macOS-Style Siri Overlay Modal */}
      <div
        className="siri-floating-overlay"
        style={{
          width: isMinimized ? '340px' : '460px',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Apple Window Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 18px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            background: 'rgba(255, 255, 255, 0.03)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Apple Window Traffic Light Controls */}
            <div style={{ display: 'flex', gap: '6px' }}>
              <div
                onClick={handleDismissSiri}
                style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444', cursor: 'pointer' }}
                title="Close Siri (Esc)"
              />
              <div
                onClick={() => setIsMinimized(!isMinimized)}
                style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#eab308', cursor: 'pointer' }}
                title="Minimize / Expand"
              />
              <div
                onClick={handleStartActiveListening}
                style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#22c55e', cursor: 'pointer' }}
                title="Talk to Siri"
              />
            </div>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e2e8f0', letterSpacing: '0.04em', marginLeft: '6px' }}>
              SIRI WORKFLOW AGENT
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setIsHeySiriListening(!isHeySiriListening)}
              style={{
                background: 'transparent',
                border: 'none',
                color: isHeySiriListening ? '#38bdf8' : '#64748b',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
                fontWeight: 600,
              }}
              title="Toggle Hands-Free 'Hey Siri' listening mode"
            >
              <Radio size={12} color={isHeySiriListening ? '#38bdf8' : '#64748b'} />
              <span>{isHeySiriListening ? 'Wake On' : 'Wake Off'}</span>
            </button>
            <button
              onClick={handleDismissSiri}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Live Hardware Telemetry HUD Bar */}
        {telemetry && !isMinimized && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              padding: '8px 12px',
              background: 'rgba(0, 0, 0, 0.35)',
              borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: '0.72rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38bdf8' }}>
              <Cpu size={12} />
              <span>CPU: {telemetry.cpu.usage_percent}%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#818cf8' }}>
              <Activity size={12} />
              <span>RAM: {telemetry.ram.usage_percent}%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#34d399' }}>
              <HardDrive size={12} />
              <span>Disk: {telemetry.disk.free_gb}GB</span>
            </div>
            {telemetry.battery && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b' }}>
                <Battery size={12} />
                <span>{telemetry.battery.percent}%</span>
              </div>
            )}
          </div>
        )}

        {/* Scrollable Body */}
        <div style={{ overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Siri Orb Centerpiece */}
          <VoiceOrb
            state={voiceState}
            onToggleRecording={voiceState === 'LISTENING' ? stopActiveRecording : handleStartActiveListening}
            onInterrupt={stopAudio}
            onRetry={handleStartActiveListening}
            transcript={transcript}
            latestAnswer={latestAnswer}
            onReplayAudio={latestAudio ? () => playSiriAudio(latestAudio) : undefined}
            isHeySiriActive={isHeySiriListening}
            onToggleHeySiri={() => setIsHeySiriListening(!isHeySiriListening)}
            error={errorMessage || undefined}
          />

          {/* Autonomous Tool Execution Badge */}
          {executedTools.length > 0 && !isMinimized && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: '12px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.72rem', color: '#818cf8', fontWeight: 700, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Terminal size={13} /> Autonomous PC Workflow Action: {agentActionType || 'COMPLETED'}
                </span>
                <CheckCircle2 size={13} color="#34d399" />
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {executedTools.map((t, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      fontSize: '0.7rem',
                      color: '#cbd5e1',
                    }}
                  >
                    ⚙️ {t.tool} ({t.time_ms}ms)
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Quick PC Workflow Action Chips */}
          {!isMinimized && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Quick PC Automation Workflows (1-Click or Voice):
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {[
                  { label: '⚡ Check Hardware', prompt: 'Check my laptop CPU, memory and battery status' },
                  { label: '📊 Top Processes', prompt: 'Show top running processes consuming memory' },
                  { label: '📂 Search Workspace', prompt: 'Find all markdown and project files' },
                  { label: '🧹 Clean Temp Cache', prompt: 'Clean temporary cache and free disk space' },
                  { label: '📝 Audit Report', prompt: 'Generate an executive PC health report' },
                ].map((act, i) => (
                  <button
                    key={i}
                    onClick={() => handleRunAgentWorkflow(act.prompt)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '4px 10px',
                      color: '#cbd5e1',
                      fontSize: '0.72rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)')}
                  >
                    {act.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Citations Card if returned from RAG */}
          {citations && citations.length > 0 && !isMinimized && (
            <div
              style={{
                padding: '12px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <span style={{ fontSize: '0.72rem', color: '#818cf8', display: 'block', marginBottom: '6px', fontWeight: 700, textTransform: 'uppercase' }}>
                Verified Document Sources ({citations.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {citations.slice(0, 2).map((c, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                    <span style={{ color: '#38bdf8', fontWeight: 600 }}>• {c.filename || 'Document'}</span> (Page {c.page || 1}):
                    <p style={{ margin: '2px 0 0 8px', color: '#94a3b8', fontStyle: 'italic', fontSize: '0.74rem' }}>
                      "{c.snippet}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
