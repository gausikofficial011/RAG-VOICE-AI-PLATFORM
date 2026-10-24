import React, { useEffect, useState } from 'react';
import { Mic, MicOff, Square, RefreshCw, Volume2, Sparkles, Radio } from 'lucide-react';

export type VoiceState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'THINKING' | 'SPEAKING';

interface VoiceOrbProps {
  state: VoiceState;
  onToggleRecording: () => void;
  onInterrupt: () => void;
  onRetry: () => void;
  confidence?: number;
  transcript?: string;
  latestAnswer?: string;
  onReplayAudio?: () => void;
  isHeySiriActive?: boolean;
  onToggleHeySiri?: () => void;
  error?: string;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  state,
  onToggleRecording,
  onInterrupt,
  onRetry,
  confidence,
  transcript,
  latestAnswer,
  onReplayAudio,
  isHeySiriActive = true,
  onToggleHeySiri,
  error,
}) => {
  const [waveHeights, setWaveHeights] = useState<number[]>([14, 28, 22, 38, 26, 34, 18, 36, 28, 20, 16, 24, 30, 18]);

  // Dynamic waveform simulation based on active voice state
  useEffect(() => {
    if (state === 'LISTENING' || state === 'SPEAKING') {
      const interval = setInterval(() => {
        setWaveHeights(
          Array.from({ length: 14 }, () =>
            Math.floor(Math.random() * (state === 'LISTENING' ? 44 : 32) + 8)
          )
        );
      }, 80);
      return () => clearInterval(interval);
    } else {
      setWaveHeights([6, 10, 14, 18, 22, 16, 12, 16, 22, 18, 14, 10, 8, 6]);
    }
  }, [state]);

  const strandGradients = [
    'linear-gradient(to top, #06b6d4, #38bdf8)',
    'linear-gradient(to top, #3b82f6, #60a5fa)',
    'linear-gradient(to top, #6366f1, #818cf8)',
    'linear-gradient(to top, #8b5cf6, #a78bfa)',
    'linear-gradient(to top, #a855f7, #c084fc)',
    'linear-gradient(to top, #d946ef, #e879f9)',
    'linear-gradient(to top, #ec4899, #f472b6)',
    'linear-gradient(to top, #f43f5e, #fb7185)',
    'linear-gradient(to top, #fb7185, #f472b6)',
    'linear-gradient(to top, #c084fc, #a855f7)',
    'linear-gradient(to top, #818cf8, #6366f1)',
    'linear-gradient(to top, #38bdf8, #06b6d4)',
    'linear-gradient(to top, #10b981, #34d399)',
    'linear-gradient(to top, #06b6d4, #38bdf8)',
  ];

  const stateSubtitles: Record<VoiceState, string> = {
    IDLE: isHeySiriActive ? 'Say "Hey Siri" or tap to talk' : 'Tap to speak',
    LISTENING: 'Go ahead, I’m listening...',
    PROCESSING: 'Transcribing speech...',
    THINKING: 'Searching enterprise intelligence...',
    SPEAKING: 'AI Assistant speaking...',
  };

  return (
    <>
      {/* Full-Screen Apple Intelligence Perimeter Rainbow Glow when Siri is Active */}
      {state !== 'IDLE' && <div className="siri-screen-perimeter-glow" />}

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '18px 16px', gap: '14px' }}>
        {/* Apple "Hey Siri" Mode Bar & Keyboard Shortcut Banner */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '20px',
              background: isHeySiriActive ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${isHeySiriActive ? 'rgba(56, 189, 248, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
              fontSize: '0.78rem',
              color: isHeySiriActive ? '#38bdf8' : '#94a3b8',
              fontWeight: 600,
              cursor: onToggleHeySiri ? 'pointer' : 'default',
            }}
            onClick={onToggleHeySiri}
            title="Click to toggle always-listening 'Hey Siri' wake word"
          >
            <Radio size={13} color={isHeySiriActive ? '#38bdf8' : '#64748b'} style={{ animation: isHeySiriActive ? 'pulse 2s infinite' : 'none' }} />
            <span>"Hey Siri" Hands-Free: {isHeySiriActive ? 'Listening' : 'Paused'}</span>
          </div>

          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={12} color="#818cf8" />
            <span>Laptop Shortcut: <b>Alt + S</b> or say <b>"Hey Siri"</b></span>
          </span>
        </div>

        {/* Photorealistic Apple Siri Liquid Plasma Orb */}
        <div
          className={`siri-orb-wrapper ${state.toLowerCase()}`}
          onClick={state === 'SPEAKING' ? onInterrupt : onToggleRecording}
          title={state === 'SPEAKING' ? 'Click to interrupt' : 'Click to speak or say "Hey Siri"'}
        >
          {/* Outer Breathing Iridescent Glow */}
          <div className="siri-orb-outer-glow" />

          {/* Core Glass Sphere */}
          <div className="siri-orb-core">
            {/* Layer 1: Swirling Conic Iridescent Plasma */}
            <div className="siri-plasma-layer" />

            {/* Layer 2: Counter-Rotating Secondary Nebula */}
            <div className="siri-nebula-layer" />

            {/* Layer 3: Specular Highlight Dome */}
            <div className="siri-specular-glass" />

            {/* Layer 4: Deep Shadow Vignette */}
            <div className="siri-vignette" />

            {/* Central Iconic Microphone/Speaker Symbol */}
            <div style={{ position: 'relative', zIndex: 5, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {state === 'LISTENING' && <Mic size={44} color="#ffffff" style={{ filter: 'drop-shadow(0 0 10px rgba(255,255,255,0.8))' }} />}
              {state === 'SPEAKING' && <Volume2 size={44} color="#ffffff" style={{ filter: 'drop-shadow(0 0 10px rgba(255,255,255,0.8))' }} />}
              {(state === 'PROCESSING' || state === 'THINKING') && (
                <RefreshCw size={40} color="#ffffff" style={{ animation: 'spin 1.2s linear infinite', filter: 'drop-shadow(0 0 12px rgba(255,255,255,0.9))' }} />
              )}
              {state === 'IDLE' && <Mic size={44} color="#ffffff" style={{ opacity: 0.9, filter: 'drop-shadow(0 0 8px rgba(255,255,255,0.5))' }} />}
            </div>
          </div>
        </div>

        {/* State Status Badge */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
          <span
            style={{
              fontSize: '0.86rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.14em',
              background: 'linear-gradient(90deg, #38bdf8, #c084fc, #f472b6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {state === 'IDLE' ? 'SIRI STANDBY' : `SIRI ${state}`}
          </span>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', fontWeight: 500, margin: 0 }}>
            {stateSubtitles[state]}
          </p>
        </div>

        {/* Apple Multi-Colored Fluid Acoustic Waveform */}
        <div className="siri-fluid-waveform">
          {waveHeights.map((h, i) => (
            <div
              key={i}
              className="siri-wave-strand"
              style={{
                height: `${h}px`,
                background: strandGradients[i % strandGradients.length],
                opacity: state === 'IDLE' ? 0.35 : 0.95,
              }}
            />
          ))}
        </div>

        {/* Live Transcribed Input Display */}
        {transcript && (
          <div
            className="glass-panel"
            style={{
              maxWidth: '620px',
              width: '100%',
              padding: '12px 18px',
              textAlign: 'center',
              fontSize: '0.92rem',
              color: '#e2e8f0',
              borderLeft: '4px solid #38bdf8',
              background: 'rgba(15, 23, 42, 0.75)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: '#38bdf8', display: 'block', marginBottom: '2px', textTransform: 'uppercase', fontWeight: 700 }}>
              Transcribed Speech {confidence ? `(${(confidence * 100).toFixed(0)}%)` : ''}
            </span>
            "{transcript}"
          </div>
        )}

        {/* Live AI Response Display */}
        {latestAnswer && (
          <div
            className="glass-panel"
            style={{
              maxWidth: '620px',
              width: '100%',
              padding: '14px 18px',
              textAlign: 'left',
              fontSize: '0.92rem',
              color: '#f8fafc',
              borderLeft: '4px solid #10b981',
              background: 'rgba(16, 185, 129, 0.08)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.72rem', color: '#34d399', textTransform: 'uppercase', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Volume2 size={14} /> Siri Intelligence Response {state === 'SPEAKING' ? '(Speaking...)' : ''}
              </span>
              {onReplayAudio && (
                <button
                  onClick={onReplayAudio}
                  style={{
                    background: 'rgba(52, 211, 153, 0.1)',
                    border: '1px solid rgba(52, 211, 153, 0.3)',
                    borderRadius: '6px',
                    color: '#34d399',
                    fontSize: '0.72rem',
                    padding: '3px 10px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontWeight: 600,
                  }}
                >
                  <Volume2 size={12} /> Replay
                </button>
              )}
            </div>
            <p style={{ margin: 0, lineHeight: '1.6' }}>{latestAnswer}</p>
          </div>
        )}

        {/* Interactive Apple-Style Pill Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
          {state === 'SPEAKING' && (
            <button className="btn-secondary" onClick={onInterrupt} style={{ borderColor: '#ef4444', color: '#f87171', borderRadius: '24px', padding: '8px 18px' }}>
              <Square size={15} /> Stop Speaking
            </button>
          )}
          {state === 'LISTENING' && (
            <button className="btn-secondary" onClick={onToggleRecording} style={{ borderColor: '#38bdf8', color: '#38bdf8', borderRadius: '24px', padding: '8px 18px' }}>
              <MicOff size={15} /> Done Speaking
            </button>
          )}
          {state === 'IDLE' && (
            <button className="btn-primary" onClick={onToggleRecording} style={{ borderRadius: '24px', padding: '8px 20px', background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%)' }}>
              <Mic size={15} /> Ask Siri Now
            </button>
          )}
          {error && (
            <button className="btn-secondary" onClick={onRetry} style={{ borderRadius: '24px', padding: '8px 16px' }}>
              <RefreshCw size={15} /> Retry
            </button>
          )}
        </div>

        {error && (
          <p style={{ color: '#f87171', fontSize: '0.85rem', margin: 0 }}>{error}</p>
        )}
      </div>
    </>
  );
};
