"""
Voice Activity Detection (VAD) & Audio Quality Detector
Analyzes audio frames to detect speech vs silence, background noise level, and signal quality.
"""

from typing import Dict, List, Tuple, Any
import math
import struct


class AudioActivityDetector:
    def __init__(self, silence_threshold_rms: float = 0.02, min_speech_duration_ms: int = 250):
        self.silence_threshold_rms = silence_threshold_rms
        self.min_speech_duration_ms = min_speech_duration_ms

    def compute_rms(self, pcm_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy level of 16-bit PCM audio."""
        if not pcm_bytes:
            return 0.0
        # 16-bit signed PCM samples
        sample_count = len(pcm_bytes) // 2
        if sample_count == 0:
            return 0.0
        try:
            samples = struct.unpack(f"<{sample_count}h", pcm_bytes[: sample_count * 2])
            sum_squares = sum((s / 32768.0) ** 2 for s in samples)
            return math.sqrt(sum_squares / sample_count)
        except Exception:
            return 0.0

    def analyze_audio_quality(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Estimate SNR, noise floor, speech presence, and quality advice.
        """
        rms = self.compute_rms(audio_bytes)
        is_speech = rms > self.silence_threshold_rms

        if rms < 0.005:
            quality = "TOO_QUIET"
            advice = "Please move closer to the microphone and try again."
        elif rms > 0.85:
            quality = "CLIPPING"
            advice = "Audio level is too loud. Please lower microphone gain."
        else:
            quality = "OPTIMAL"
            advice = "Audio quality is clear."

        return {
            "rms_energy": round(rms, 4),
            "is_speech": is_speech,
            "quality": quality,
            "advice": advice,
        }


vad_detector = AudioActivityDetector()
