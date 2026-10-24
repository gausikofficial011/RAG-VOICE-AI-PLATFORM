"""
Voice AI Service API Router
End-to-End Voice Pipeline: VAD -> STT -> Language Detection -> RAG -> TTS -> Latency Profiling.
"""

import time
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.knowledge_base import KnowledgeBase
from sqlalchemy import select
from backend.app.voice.vad import vad_detector
from backend.app.voice.stt import stt_provider
from backend.app.voice.tts import tts_provider
from backend.app.rag.pipeline import rag_pipeline
from backend.app.auth.dependencies import get_current_user
from ml.language_detection.detector import language_detector

router = APIRouter(prefix="/voice", tags=["Voice AI"])


@router.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze incoming audio for speech activity and noise quality."""
    audio_bytes = await file.read()
    analysis = vad_detector.analyze_audio_quality(audio_bytes)
    return analysis


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Convert audio stream to text with language detection."""
    audio_bytes = await file.read()
    stt_res = await stt_provider.transcribe(audio_bytes, language)
    lang_info = language_detector.detect(stt_res["transcript"])
    return {
        "transcript": stt_res["transcript"],
        "confidence": stt_res["confidence"],
        "language": lang_info["language"],
        "language_name": lang_info["name"],
    }


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    language: Optional[str] = Form("en"),
):
    """Synthesize text into speech audio."""
    audio_b64 = await tts_provider.synthesize_base64(text, language or "en")
    return {"audio_base64": audio_b64}


@router.post("/query")
async def voice_query(
    kb_id: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
    transcript_text: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete end-to-end Voice RAG interaction:
    Microphone Audio -> VAD & Quality Check -> STT -> Language Detect -> Hybrid RAG -> TTS Audio.
    """
    total_start = time.perf_counter()
    audio_bytes = await file.read()

    # Automatic fallback to first KB if none provided or invalid
    if not kb_id or str(kb_id).strip() in ["undefined", "null", ""]:
        stmt_kb = select(KnowledgeBase.id).where(KnowledgeBase.tenant_id == current_user.tenant_id).order_by(KnowledgeBase.created_at.asc())
        res_kb = await db.execute(stmt_kb)
        first_kb = res_kb.scalar_one_or_none()
        if first_kb:
            kb_id = first_kb

    # 1. VAD & Quality Check
    t0 = time.perf_counter()
    quality_analysis = vad_detector.analyze_audio_quality(audio_bytes)
    vad_ms = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Speech-to-Text
    t1 = time.perf_counter()
    if transcript_text and transcript_text.strip():
        transcript = transcript_text.strip()
        stt_ms = round((time.perf_counter() - t1) * 1000, 2)
    else:
        stt_res = await stt_provider.transcribe(audio_bytes, language)
        stt_ms = round((time.perf_counter() - t1) * 1000, 2)
        transcript = stt_res.get("transcript", "")

    if not transcript:
        return {
            "transcript": "",
            "answer": "I did not detect any speech. Please check your microphone and speak clearly.",
            "audio_base64": None,
            "citations": [],
            "latency": {"vad_ms": vad_ms, "stt_ms": stt_ms, "total_ms": round((time.perf_counter() - total_start) * 1000, 2)},
        }

    # 3. Multilingual Detection
    lang_info = language_detector.detect(transcript)
    detected_lang = lang_info["language"]

    # 4. Hybrid RAG Pipeline
    rag_res = await rag_pipeline.execute(
        tenant_id=current_user.tenant_id,
        query=transcript,
        kb_id=kb_id,
        audio_requested=True,
        language=detected_lang,
    )

    rag_latency = rag_res["latency"]
    rag_latency["vad_ms"] = vad_ms
    rag_latency["stt_ms"] = stt_ms
    rag_latency["total_ms"] = round((time.perf_counter() - total_start) * 1000, 2)

    return {
        "transcript": transcript,
        "language": detected_lang,
        "language_name": lang_info["name"],
        "answer": rag_res["answer"],
        "intent": rag_res["intent"],
        "retrieval_strategy": rag_res["retrieval_strategy"],
        "grounding_score": rag_res["grounding_score"],
        "grounding_status": rag_res["grounding_status"],
        "citations": rag_res["citations"],
        "audio_base64": rag_res.get("audio_base64"),
        "latency": rag_latency,
        "quality_advice": quality_analysis.get("advice"),
    }
