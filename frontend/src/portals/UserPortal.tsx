import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { siriSounds } from '../services/siriSounds';
import type { KnowledgeBase, DocumentItem, ChatMessage } from '../types';
import { VoiceOrb, type VoiceState } from '../components/VoiceOrb';
import { TraceViewer } from '../components/TraceViewer';
import { DocumentViewerModal } from '../components/DocumentViewerModal';
import {
  Send,
  Upload,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Volume2,
  Trash2,
  BookOpen,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface UserPortalProps {
  knowledgeBases: KnowledgeBase[];
  selectedKBId: string | null;
  onRefreshKBs: () => void;
}

export const UserPortal: React.FC<UserPortalProps> = ({
  knowledgeBases,
  selectedKBId,
  onRefreshKBs,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [latestAnswer, setLatestAnswer] = useState<string>('');
  const [latestAudio, setLatestAudio] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<{ docId: string; filename: string; page: number; snippet: string } | null>(null);
  const [activeTraceMessage, setActiveTraceMessage] = useState<ChatMessage | null>(null);
  const [showVoiceOrb, setShowVoiceOrb] = useState(true);

  // Audio recording & playback refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const speechRecognitionRef = useRef<any>(null);
  const recognizedTranscriptRef = useRef<string>('');

  const effectiveKBId = selectedKBId || (knowledgeBases.length > 0 ? knowledgeBases[0].id : null);

  useEffect(() => {
    if (effectiveKBId) {
      loadDocuments(effectiveKBId);
    }
  }, [effectiveKBId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadDocuments(kbId: string) {
    try {
      const docs = await api.getDocuments(kbId);
      setDocuments(docs);
    } catch (e) {
      console.error('Failed to load documents', e);
    }
  }

  // Handle Document Upload
  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files || e.target.files.length === 0 || !effectiveKBId) return;
    const file = e.target.files[0];
    try {
      setUploading(true);
      await api.uploadDocument(effectiveKBId, file);
      await loadDocuments(effectiveKBId);
      onRefreshKBs();
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  }

  // Delete Document
  async function handleDeleteDocument(docId: string) {
    if (!confirm('Are you sure you want to delete this document and all its indexed vectors?')) return;
    try {
      await api.deleteDocument(docId);
      if (effectiveKBId) await loadDocuments(effectiveKBId);
      onRefreshKBs();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  // Play audio base64 with interruption support
  function playAudio(audioBase64: string) {
    stopAudio();
    try {
      const audio = new Audio(audioBase64);
      currentAudioRef.current = audio;
      setVoiceState('SPEAKING');

      audio.onended = () => {
        setVoiceState('IDLE');
      };
      audio.onerror = (e) => {
        console.warn('Audio playback error', e);
        setVoiceState('IDLE');
      };
      audio.play().catch((err) => {
        console.warn('Audio play request interrupted or prevented by browser policy:', err);
        setVoiceState('IDLE');
      });
    } catch (e) {
      console.error('Audio playback failed to initialize', e);
      setVoiceState('IDLE');
    }
  }

  function replayAudio() {
    if (latestAudio) {
      playAudio(latestAudio);
    }
  }

  function stopAudio() {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setVoiceState('IDLE');
  }

  // Text Query Execution
  async function handleSubmitQuery(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const query = inputQuery.trim();
    setInputQuery('');
    setLoading(true);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await api.queryRAG({
        query,
        kb_id: effectiveKBId || undefined,
        audio_requested: true,
      });

      const assistantMsg: ChatMessage = {
        id: res.message_id || `asst-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        intent: res.intent,
        grounding_score: res.grounding_score,
        grounding_status: res.grounding_status,
        citations: res.citations,
        latency: res.latency,
        audio_base64: res.audio_base64,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setActiveTraceMessage(assistantMsg);

      setLatestAnswer(res.answer);
      if (res.audio_base64) {
        setLatestAudio(res.audio_base64);
        playAudio(res.audio_base64);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'system',
        content: `Error: ${err.message}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  // Voice Recording Toggle with Browser Speech Recognition + Backend Edge-TTS
  async function handleToggleVoiceRecording() {
    if (voiceState === 'LISTENING') {
      // Stop recording
      if (speechRecognitionRef.current) {
        try { speechRecognitionRef.current.stop(); } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    // Start Recording
    try {
      siriSounds.playWakeChime();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      recognizedTranscriptRef.current = '';
      setTranscript('');
      setLatestAnswer('');

      // Real-time browser speech recognition for zero-latency user transcription
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';
          recognition.onresult = (event: any) => {
            let fullText = '';
            for (let i = 0; i < event.results.length; i++) {
              fullText += event.results[i][0].transcript;
            }
            if (fullText) {
              recognizedTranscriptRef.current = fullText;
              setTranscript(fullText);
            }
          };
          recognition.onerror = (e: any) => console.log('SpeechRecognition notice:', e);
          recognition.start();
          speechRecognitionRef.current = recognition;
        } catch (e) {
          console.warn('SpeechRecognition initialization error:', e);
        }
      }

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        if (speechRecognitionRef.current) {
          try { speechRecognitionRef.current.stop(); } catch {}
          speechRecognitionRef.current = null;
        }
        setVoiceState('PROCESSING');

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const finalTranscript = recognizedTranscriptRef.current.trim();
        try {
          setVoiceState('THINKING');
          const res = await api.voiceQuery(
            audioBlob,
            effectiveKBId || undefined,
            undefined,
            'en',
            finalTranscript || undefined
          );

          setTranscript(res.transcript || finalTranscript || '');

          const userMsg: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: res.transcript || finalTranscript || 'Spoken Voice Query',
            created_at: new Date().toISOString(),
          };

          const assistantMsg: ChatMessage = {
            id: `asst-${Date.now()}`,
            role: 'assistant',
            content: res.answer,
            intent: res.intent,
            grounding_score: res.grounding_score,
            grounding_status: res.grounding_status,
            citations: res.citations,
            latency: res.latency,
            audio_base64: res.audio_base64,
            created_at: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, userMsg, assistantMsg]);
          setActiveTraceMessage(assistantMsg);
          setLatestAnswer(res.answer);

          if (res.audio_base64) {
            setLatestAudio(res.audio_base64);
            playAudio(res.audio_base64);
          } else {
            setVoiceState('IDLE');
          }
        } catch (err: any) {
          alert(`Voice query failed: ${err.message}`);
          setVoiceState('IDLE');
        }
      };

      mediaRecorder.start();
      setVoiceState('LISTENING');
    } catch (err: any) {
      alert(`Microphone access error: ${err.message}`);
      setVoiceState('IDLE');
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', minHeight: 'calc(100vh - 68px)', gap: '1px', background: 'var(--border-subtle)' }}>
      {/* Sidebar: Documents & Knowledge Bases */}
      <aside style={{ background: '#090d16', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          {(() => {
            const activeKB = knowledgeBases.find((k) => k.id === selectedKBId);
            return (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div>
                  <h2 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Knowledge Base
                  </h2>
                  {activeKB && (
                    <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600 }}>{activeKB.name}</span>
                  )}
                </div>
                <label className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer' }}>
                  <Upload size={13} /> {uploading ? 'Processing...' : 'Upload'}
                  <input type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt,.csv,.md,.html,.json" style={{ display: 'none' }} disabled={uploading || !selectedKBId} />
                </label>
              </div>
            );
          })()}

          {!selectedKBId ? (
            <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Select or create a knowledge base to begin.</p>
          ) : (
            <div>
              <span style={{ fontSize: '0.8rem', color: '#818cf8', display: 'block', marginBottom: '10px' }}>
                {documents.length} Indexed Document{documents.length !== 1 ? 's' : ''}
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '55vh', overflowY: 'auto' }}>
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="glass-panel"
                    style={{
                      padding: '10px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.85rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                      <FileText size={16} color="#6366f1" style={{ flexShrink: 0 }} />
                      <span style={{ color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={doc.filename}>
                        {doc.filename}
                      </span>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      title="Delete document"
                      style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '2px' }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Interaction Area */}
      <main style={{ background: '#090d16', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 68px)' }}>
        {/* Toggleable Voice Orb Header */}
        <div style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(15, 23, 42, 0.4)' }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px 24px' }}>
            <button
              onClick={() => setShowVoiceOrb(!showVoiceOrb)}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}
            >
              {showVoiceOrb ? <ChevronUp size={14} /> : <ChevronDown size={14} />} {showVoiceOrb ? 'Hide Voice Interface' : 'Show Voice Interface'}
            </button>
          </div>
          {showVoiceOrb && (
            <VoiceOrb
              state={voiceState}
              onToggleRecording={handleToggleVoiceRecording}
              onInterrupt={stopAudio}
              onRetry={handleToggleVoiceRecording}
              transcript={transcript}
              latestAnswer={latestAnswer}
              onReplayAudio={latestAudio ? replayAudio : undefined}
            />
          )}
        </div>

        {/* Chat Message Scroll */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {messages.length === 0 ? (
            <div style={{ margin: 'auto', textAlign: 'center', maxWidth: '480px', color: '#64748b' }}>
              <BookOpen size={48} color="#6366f1" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
                Ask Anything About Your Documents
              </h3>
              <p style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                Speak into your microphone or type a question below. Answers are strictly grounded in your private documents with exact citations.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '75%',
                }}
              >
                <div
                  className="glass-panel"
                  style={{
                    padding: '16px 20px',
                    borderRadius: '16px',
                    background: msg.role === 'user' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.3))' : 'rgba(17, 24, 39, 0.7)',
                    borderColor: msg.role === 'user' ? 'rgba(99, 102, 241, 0.3)' : 'var(--border-subtle)',
                  }}
                >
                  <p style={{ color: '#f8fafc', fontSize: '0.95rem', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </p>

                  {/* Grounding & Citations block for Assistant */}
                  {msg.role === 'assistant' && (
                    <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      {msg.intent === 'PC_AGENT_ACTION' && (
                        <div style={{ marginBottom: '8px' }}>
                          <span
                            style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              background: 'rgba(99, 102, 241, 0.2)',
                              color: '#818cf8',
                              border: '1px solid rgba(99, 102, 241, 0.4)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            ⚡ PC WORKFLOW AGENT EXECUTED
                          </span>
                        </div>
                      )}
                      {msg.grounding_score !== undefined && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                          <span
                            style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              background: msg.grounding_score >= 0.7 ? 'rgba(52, 211, 153, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                              color: msg.grounding_score >= 0.7 ? '#34d399' : '#f59e0b',
                            }}
                          >
                            GROUNDING: {msg.grounding_status || 'SUPPORTED'} ({(msg.grounding_score * 100).toFixed(0)}%)
                          </span>
                          {msg.latency && (
                            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                              Latency: {msg.latency.total_ms}ms
                            </span>
                          )}
                        </div>
                      )}

                      {/* Citations List */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
                          {msg.citations.map((c, i) => (
                            <button
                              key={i}
                              onClick={() => setSelectedCitation({ docId: c.document_id, filename: c.filename, page: c.page, snippet: c.snippet })}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '0.75rem', gap: '6px' }}
                            >
                              <ExternalLink size={12} />
                              Source {i + 1}: {c.filename} (p. {c.page})
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Action buttons (Listen, Trace, Feedback) */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
                        {msg.audio_base64 && (
                          <button
                            onClick={() => msg.audio_base64 && playAudio(msg.audio_base64)}
                            className="btn-secondary"
                            style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          >
                            <Volume2 size={13} /> Listen
                          </button>
                        )}
                        <button
                          onClick={() => setActiveTraceMessage(msg)}
                          className="btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        >
                          View RAG Trace
                        </button>
                        <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px' }}>
                          <button
                            onClick={() => api.submitFeedback({ message_id: msg.id, rating: 1, feedback_type: 'HELPFUL' })}
                            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                            title="Helpful answer"
                          >
                            <ThumbsUp size={14} />
                          </button>
                          <button
                            onClick={() => api.submitFeedback({ message_id: msg.id, rating: -1, feedback_type: 'INCORRECT' })}
                            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                            title="Unhelpful answer"
                          >
                            <ThumbsDown size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* PC Agent Quick-Action Automation Toolbar */}
        <div
          style={{
            padding: '8px 24px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.45)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            overflowX: 'auto',
          }}
        >
          <span style={{ fontSize: '0.72rem', color: '#818cf8', fontWeight: 700, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
            ⚡ PC Agent:
          </span>
          {[
            { label: 'Check CPU & RAM', prompt: 'Check my laptop CPU, memory and battery status' },
            { label: 'Top Tasks', prompt: 'Show top running processes consuming memory' },
            { label: 'Search Files', prompt: 'Find all markdown and project files' },
            { label: 'Clean Temp', prompt: 'Clean temporary cache and free disk space' },
            { label: 'Generate Report', prompt: 'Generate an executive PC health report' },
          ].map((action, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setInputQuery(action.prompt);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '14px',
                padding: '3px 10px',
                color: '#cbd5e1',
                fontSize: '0.74rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)')}
            >
              {action.label}
            </button>
          ))}
        </div>

        {/* Text Input Footer */}
        <form
          onSubmit={handleSubmitQuery}
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            gap: '12px',
          }}
        >
          <input
            type="text"
            className="glass-input"
            placeholder={effectiveKBId ? "Ask a grounded question across your documents..." : "Select or create a knowledge base to chat..."}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn-primary" disabled={loading || !inputQuery.trim()}>
            <Send size={16} /> Send
          </button>
        </form>

        {/* Trace Modal / Drawer */}
        {activeTraceMessage && (
          <div style={{ padding: '0 24px 20px 24px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
              <button
                onClick={() => setActiveTraceMessage(null)}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  color: '#94a3b8',
                  padding: '4px 10px',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                }}
              >
                ✕ Close Trace
              </button>
            </div>
            <TraceViewer
              query={activeTraceMessage.content}
              intent={activeTraceMessage.intent}
              retrievalStrategy="hybrid"
              groundingScore={activeTraceMessage.grounding_score}
              groundingStatus={activeTraceMessage.grounding_status}
              citations={activeTraceMessage.citations}
              latency={activeTraceMessage.latency}
            />
          </div>
        )}
      </main>

      {/* Document Viewer Modal for Citation Jumps */}
      {selectedCitation && (
        <DocumentViewerModal
          docId={selectedCitation.docId}
          filename={selectedCitation.filename}
          targetPage={selectedCitation.page}
          highlightSnippet={selectedCitation.snippet}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
};
