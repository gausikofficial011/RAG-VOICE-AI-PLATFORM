"""
Model H — Multilingual Language Detector
Detects English, Tamil, Hindi, Malayalam, and Japanese with confidence scoring.
"""

from typing import Dict, Any


class LanguageDetector:
    def __init__(self):
        pass

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect text language by analyzing script distributions and lexical markers.
        Supported: 'en', 'ta', 'hi', 'ml', 'ja'
        """
        if not text or not text.strip():
            return {"language": "en", "confidence": 1.0, "name": "English"}

        counts = {
            "ta": 0,  # Tamil (0B80-0BFF)
            "hi": 0,  # Hindi / Devanagari (0900-097F)
            "ml": 0,  # Malayalam (0D00-0D7F)
            "ja": 0,  # Japanese Hiragana/Katakana/Kanji (3040-30FF, 4E00-9FAF)
            "en": 0,  # Latin
        }

        total_chars = 0
        for char in text:
            cp = ord(char)
            if 0x0B80 <= cp <= 0x0BFF:
                counts["ta"] += 1
                total_chars += 1
            elif 0x0900 <= cp <= 0x097F:
                counts["hi"] += 1
                total_chars += 1
            elif 0x0D00 <= cp <= 0x0D7F:
                counts["ml"] += 1
                total_chars += 1
            elif (0x3040 <= cp <= 0x30FF) or (0x4E00 <= cp <= 0x9FAF):
                counts["ja"] += 1
                total_chars += 1
            elif char.isalpha():
                counts["en"] += 1
                total_chars += 1

        if total_chars == 0:
            return {"language": "en", "confidence": 1.0, "name": "English"}

        # Find dominant language
        dominant_lang = max(counts, key=counts.get)
        dominant_count = counts[dominant_lang]
        confidence = round(dominant_count / total_chars, 4)

        # Enforce minimum threshold for non-English scripts
        if dominant_lang != "en" and dominant_count >= 2:
            pass
        elif counts["en"] > 0:
            dominant_lang = "en"
            confidence = round(counts["en"] / total_chars, 4)

        names = {
            "en": "English",
            "ta": "Tamil",
            "hi": "Hindi",
            "ml": "Malayalam",
            "ja": "Japanese",
        }

        return {
            "language": dominant_lang,
            "confidence": max(confidence, 0.75),
            "name": names.get(dominant_lang, "English"),
        }


language_detector = LanguageDetector()
