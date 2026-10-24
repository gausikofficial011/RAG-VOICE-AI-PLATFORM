# Voice Pipeline & Speech AI Guide

## 1. Overview & Voice Orb UX

The voice interface bridges conversational audio with grounded document intelligence. The frontend user experience centers around the **AI Voice Orb**, which dynamically renders audio amplitude pulses and transitions across 5 operational states:

1. **`IDLE`**: Calm glowing gradient orb awaiting microphone activation.
2. **`LISTENING`**: Real-time microphone audio sampling with live waveform visualization bars.
3. **`PROCESSING`**: Audio packaging, RMS Voice Activity Detection, and Speech-to-Text transcription.
4. **`THINKING`**: Hybrid retrieval, reranking, LLM evidence generation, and grounding check.
5. **`SPEAKING`**: Audio synthesis playback with active rhythmic pulsing.

```
       [IDLE]
         │ (Mic Click)
         ▼
    [LISTENING] ────(User finishes speaking / Silence detected)──┐
         │                                                      ▼
    [PROCESSING] ──(Transcribed)──> [THINKING] ──(Synthesized)─> [SPEAKING]
                                                                    │
                                                               (Playback Ends)
                                                                    ▼
                                                                 [IDLE]
```

---

## 2. Voice Activity Detection (VAD) & Audio Quality Assessment

Before passing raw audio to compute-intensive Speech-to-Text engines, the audio passes through the `AudioVADProcessor` (`backend/app/voice/vad.py`):

### Quality & Speech Metrics Computed:
- **Root Mean Square (RMS) Energy**:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x[i]^2}$$
  Ensures the audio contains sufficient vocal energy ($> 0.005$) and is not silent or background noise.
- **Signal-to-Noise Ratio (SNR)**:
  Estimates vocal power relative to the initial 200ms background noise floor.
- **Audio Clipping Detection**:
  Monitors whether sample amplitudes saturate at $\pm 1.0$ (or $\pm 32767$ in 16-bit PCM), which indicates microphone gain distortion.
- **Format Normalization**:
  Converts arbitrary inputs (WAV, WebM, MP3) to standard mono 16 kHz 16-bit PCM for optimal STT accuracy.

---

## 3. Speech-to-Text (STT) Subsystem

The STT service (`backend/app/voice/stt.py`) converts acoustic input into text:
- **Primary Engine**: OpenAI Whisper / Faster-Whisper with beam search decoding.
- **Input Sampling**: 16,000 Hz, 16-bit Mono.
- **Language Auto-Detection**: Accurately handles multilingual speech across English, Japanese, Hindi, Tamil, and Spanish.
- **Confidence Scoring**: Each transcribed segment includes an average log-probability and confidence score ($0.0 \dots 1.0$). If confidence falls below 0.35, the user is prompted to repeat their query.

---

## 4. Text-to-Speech (TTS) Subsystem

The TTS engine (`backend/app/voice/tts.py`) streams natural, human-sounding synthesized audio:
- **Engine**: Microsoft Edge Neural TTS (`edge-tts`).
- **Zero API Cost & Ultra-Low Latency**: Directly produces neural MP3 audio streams without external paid subscriptions.
- **Multilingual Neural Voices**:
  - English: `en-US-GuyNeural`, `en-US-AriaNeural`, `en-GB-SoniaNeural`
  - Japanese: `ja-JP-KeitaNeural`, `ja-JP-NanamiNeural`
  - Hindi: `hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`
  - Tamil: `ta-IN-PallaviNeural`
- **Fallback Audio Chime**: If network access or the TTS service is unavailable, an in-memory synthesized sine wave audio chime (WAV) is dynamically emitted to prevent voice pipeline hangs.

---

## 5. Audio Caching & Latency Optimization

To achieve sub-500ms voice query latency:
1. **TTS Response Caching**: Commonly generated system phrases (e.g., "I found 3 relevant documents", "Please repeat your question") are cached in memory as pre-rendered MP3 buffers.
2. **Streaming Transfer**: Audio responses are streamed as `audio/mpeg` or encoded as base64 data URIs for immediate playback via the HTML5 `Audio` API.
