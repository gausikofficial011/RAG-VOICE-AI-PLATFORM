"""
Text-to-Speech (TTS) Provider
Synthesizes speech audio using edge-tts with offline WAV generation fallback.
Supports multilingual neural voices (English, Tamil, Hindi, Malayalam, Japanese).
"""

from typing import Optional, Tuple
import base64
import io
import wave
import struct
import math
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

LANGUAGE_VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "ta": "ta-IN-PallaviNeural",
    "hi": "hi-IN-SwaraNeural",
    "ml": "ml-IN-SobhanaNeural",
    "ja": "ja-JP-NanamiNeural",
}


class TTSProvider:
    def __init__(self):
        self.default_voice = settings.TTS_VOICE

    def _generate_synthetic_tone_wav(self, duration_sec: float = 1.0) -> bytes:
        """Generate a gentle synthetic acknowledgement chime (WAV format)."""
        buffer = io.BytesIO()
        sample_rate = 16000
        num_samples = int(sample_rate * duration_sec)
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            frames = []
            for i in range(num_samples):
                t = i / sample_rate
                # 440 Hz gentle sine tone with smooth decay
                amplitude = math.sin(2 * math.pi * 440 * t) * math.exp(-3 * t)
                val = int(amplitude * 16000)
                frames.append(struct.pack("<h", val))
            wf.writeframes(b"".join(frames))
        return buffer.getvalue()

    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Synthesize text to audio bytes.
        Returns: (audio_bytes, mime_type)
        """
        target_voice = voice or LANGUAGE_VOICE_MAP.get(language, self.default_voice)
        clean_text = text.replace("*", "").replace("#", "").strip()[:500]  # First 500 chars for speech

        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, target_voice)
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_data = audio_buffer.getvalue()
            if audio_data:
                return audio_data, "audio/mp3"
        except Exception as e:
            logger.warning(f"edge-tts unavailable or failed ({e}). Using audio generator fallback.")

        # Fallback to generated audio chime
        fallback_wav = self._generate_synthetic_tone_wav(duration_sec=1.2)
        return fallback_wav, "audio/wav"

    async def synthesize_base64(self, text: str, language: str = "en", voice: Optional[str] = None) -> str:
        """Return base64 Data URI."""
        audio_bytes, mime = await self.synthesize(text, language, voice)
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:{mime};base64,{b64}"


tts_provider = TTSProvider()
