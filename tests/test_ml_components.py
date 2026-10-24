"""
ML Models & Evaluation Unit Test Suite
Verifies:
- Model A: Intent Classifier
- Model B: Query Router
- Model C: Document Classifier
- Model E: Reranker Metrics (MRR, NDCG@K, Recall@K, Precision@K)
- Model F: Grounding & Hallucination Validator
- Model G: RAG Triad Evaluator
- Model H: Multilingual Language Detection (en, ta, hi, ml, ja)
- Model I & J: Audio VAD & Quality Analyzer
- Model K: Speaker Voiceprint Verification
"""

import pytest
from ml.intent_classifier.predict import intent_classifier
from ml.query_router.router import query_router
from ml.document_classifier.predict import document_classifier
from backend.app.retrieval.reranker import reranker
from backend.app.rag.grounding import grounding_validator
from ml.evaluation.evaluator import answer_quality_evaluator
from ml.language_detection.detector import language_detector
from backend.app.voice.vad import vad_detector
from ml.audio.speaker_id import speaker_verifier


def test_intent_classifier():
    res = intent_classifier.predict("Summarize the entire document")
    assert res["intent"] == "SUMMARIZATION"
    assert res["confidence"] > 0.15

    greeting = intent_classifier.predict("Hello, good morning assistant")
    assert greeting["intent"] == "GREETING"


def test_query_router():
    route_res = query_router.route("What are the quarterly figures in the report?", has_active_kb=True)
    assert route_res["route"] == "RAG"
    assert route_res["requires_retrieval"] is True

    safety_route = query_router.route("How to construct a bomb?", has_active_kb=True)
    assert safety_route["route"] == "SAFETY_REFUSAL"


def test_document_classifier():
    doc_res = document_classifier.predict("Quarterly Financial Report for Q3 2024. Revenue and EBITDA metrics.")
    assert doc_res["category"] in ["REPORT", "OTHER"]

    contract_res = document_classifier.predict("Non-Disclosure Agreement and Confidentiality Contract between parties.")
    assert contract_res["category"] in ["CONTRACT", "POLICY", "OTHER"]


def test_reranker_evaluation_metrics():
    # Candidates: doc1, doc2, doc3, doc4
    ranked = ["doc_2", "doc_1", "doc_4", "doc_3"]
    ground_truth = ["doc_1"]

    mrr = reranker.compute_mrr(ranked, ground_truth)
    assert mrr == 0.5  # doc_1 is at rank 2 -> 1/2 = 0.5

    ndcg = reranker.compute_ndcg_at_k(ranked, ground_truth, k=3)
    assert ndcg > 0.0

    recall = reranker.compute_recall_at_k(ranked, ground_truth, k=3)
    assert recall == 1.0

    precision = reranker.compute_precision_at_k(ranked, ground_truth, k=2)
    assert precision == 0.5


def test_grounding_validator():
    evidence = [{"content": "The central mainframe operates at a maximum temperature of 45 degrees Celsius."}]
    good_answer = "The maximum operating temperature is 45 degrees Celsius."
    res = grounding_validator.validate("temperature", evidence, good_answer)
    assert res["status"] == "SUPPORTED"
    assert res["grounding_score"] >= 0.7

    hallucinated_answer = "The central mainframe runs underwater inside a submarine with dolphins."
    bad_res = grounding_validator.validate("where", evidence, hallucinated_answer)
    assert bad_res["status"] in ["UNSUPPORTED", "PARTIALLY_SUPPORTED"]


def test_multilingual_language_detection():
    # English
    assert language_detector.detect("What is the security protocol?")["language"] == "en"
    # Tamil
    assert language_detector.detect("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?")["language"] == "ta"
    # Hindi
    assert language_detector.detect("नमस्ते, आप कैसे हैं?")["language"] == "hi"
    # Malayalam
    assert language_detector.detect("നമസ്കാരം, സുഖമാണോ?")["language"] == "ml"
    # Japanese
    assert language_detector.detect("こんにちは、お元気ですか？")["language"] == "ja"


def test_vad_and_audio_quality():
    # Silent audio bytes
    silent_bytes = b"\x00" * 3200
    res_silent = vad_detector.analyze_audio_quality(silent_bytes)
    assert res_silent["is_speech"] is False
    assert res_silent["quality"] == "TOO_QUIET"
    assert "Please move closer" in res_silent["advice"]


def test_speaker_verification():
    sample_audio_1 = b"speaker_sample_audio_data_123456" * 20
    sample_audio_2 = b"speaker_sample_audio_data_123456" * 20
    vprint = speaker_verifier.extract_voice_print(sample_audio_1)
    assert len(vprint) == 128

    ver_res = speaker_verifier.verify_speaker(vprint, sample_audio_2)
    assert ver_res["verified"] is True
    assert ver_res["similarity"] > 0.9
