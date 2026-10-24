"""
RAG Pipeline Orchestrator
Coordinates:
1. Intent Classification
2. Query Routing
3. Hybrid Retrieval (Dense + BM25)
4. Cross-Encoder Reranking
5. Tabular / Structured Table RAG
6. LLM Context Grounding & Generation
7. Hallucination / Grounding Validation
8. Fine-grained Citations & Provenance
9. TTS Voice Synthesis
10. Latency Waterfall Profiling
"""

import time
from typing import Any, Dict, List, Optional
from backend.app.retrieval.hybrid import hybrid_retriever
from backend.app.retrieval.reranker import reranker
from backend.app.llm.provider import llm_provider
from backend.app.rag.grounding import grounding_validator
from backend.app.rag.table_rag import table_rag_engine
from backend.app.voice.tts import tts_provider
from ml.intent_classifier.predict import intent_classifier
from ml.query_router.router import query_router


class RAGPipeline:
    def __init__(self):
        pass

    async def execute(
        self,
        tenant_id: str,
        query: str,
        kb_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        audio_requested: bool = False,
        language: str = "en",
        retrieval_strategy: str = "hybrid",
        top_k: int = 5,
        rerank_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute full RAG retrieval, generation, grounding, and latency profiling.
        """
        start_total = time.perf_counter()
        latency_breakdown = {}

        # 1. Intent Classification & Routing
        t0 = time.perf_counter()
        routing_decision = query_router.route(
            query=query,
            has_active_kb=bool(kb_id),
            has_history=bool(conversation_history),
        )
        intent = routing_decision["intent"]
        latency_breakdown["intent_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # Handle Immediate Routing decisions
        if routing_decision["route"] == "SAFETY_REFUSAL":
            answer = "I cannot fulfill this request because it violates safety guidelines or is outside the enterprise knowledge scope."
            return {
                "answer": answer,
                "intent": intent,
                "retrieval_strategy": "none",
                "grounding_score": 1.0,
                "grounding_status": "SUPPORTED",
                "citations": [],
                "latency": {**latency_breakdown, "total_ms": round((time.perf_counter() - start_total) * 1000, 2)},
                "audio_base64": None,
            }

        if routing_decision["route"] == "DIRECT_RESPONSE" and intent == "GREETING":
            if any(p in query.lower() for p in ["how are you", "are you fine", "how do you do", "how are things"]):
                answer = "Hello! I am doing great, thank you for asking! I am your voice-enabled AI assistant for your enterprise knowledge base. What can I help you find today?"
            else:
                answer = "Hello! I am your voice-enabled enterprise knowledge assistant. How can I help you today?"
            audio_b64 = await tts_provider.synthesize_base64(answer, language) if audio_requested else None
            return {
                "answer": answer,
                "intent": intent,
                "retrieval_strategy": "none",
                "grounding_score": 1.0,
                "grounding_status": "SUPPORTED",
                "citations": [],
                "latency": {**latency_breakdown, "total_ms": round((time.perf_counter() - start_total) * 1000, 2)},
                "audio_base64": audio_b64,
            }

        if routing_decision["route"] == "PC_AGENT":
            from backend.app.agent.pc_agent import pc_agent
            agent_res = await pc_agent.execute(query)
            answer = agent_res["answer"]
            audio_b64 = await tts_provider.synthesize_base64(answer, language) if audio_requested else None
            return {
                "answer": answer,
                "intent": "PC_AGENT_ACTION",
                "retrieval_strategy": "pc_agent_autonomous",
                "grounding_score": 1.0,
                "grounding_status": "SUPPORTED",
                "citations": [],
                "agent_data": agent_res["data"],
                "action_type": agent_res["action_type"],
                "executed_tools": agent_res["executed_tools"],
                "latency": {**latency_breakdown, "total_ms": round((time.perf_counter() - start_total) * 1000, 2)},
                "audio_base64": audio_b64,
            }

        # 2. Hybrid Retrieval
        t1 = time.perf_counter()
        retrieved_candidates = []
        if kb_id:
            retrieved_candidates = await hybrid_retriever.retrieve(
                tenant_id=tenant_id,
                kb_id=kb_id,
                query=query,
                top_k=top_k,
                strategy=retrieval_strategy,
            )
        latency_breakdown["retrieval_ms"] = round((time.perf_counter() - t1) * 1000, 2)

        # 3. Cross-Encoder Reranking
        t2 = time.perf_counter()
        reranked_chunks = []
        if retrieved_candidates:
            reranked_chunks = reranker.rerank(
                query=query,
                candidates=retrieved_candidates,
                top_k=rerank_k,
            )
        latency_breakdown["rerank_ms"] = round((time.perf_counter() - t2) * 1000, 2)

        # 4. Structured Tabular RAG Check (for CSV/table data)
        table_answer = None
        if retrieved_candidates and table_rag_engine.is_tabular_query(query):
            for cand in retrieved_candidates:
                content = cand.get("payload", {}).get("content", "")
                if "Row " in content or "Table Columns:" in content:
                    table_answer = table_rag_engine.process_csv_table(content, query)
                    if table_answer:
                        break

        # 5. LLM Synthesis
        t3 = time.perf_counter()
        if table_answer:
            answer = table_answer
        else:
            answer = await llm_provider.generate_response(
                query=query,
                context_chunks=reranked_chunks,
                conversation_history=conversation_history,
                language=language,
            )
        latency_breakdown["llm_ms"] = round((time.perf_counter() - t3) * 1000, 2)

        # 6. Grounding & Hallucination Validation
        t4 = time.perf_counter()
        grounding_result = grounding_validator.validate(
            query=query,
            retrieved_chunks=reranked_chunks,
            generated_answer=answer,
        )
        latency_breakdown["grounding_ms"] = round((time.perf_counter() - t4) * 1000, 2)

        # 7. Citations Assembly
        citations = []
        for c in reranked_chunks:
            p = c.get("payload", {})
            content = p.get("content", c.get("content", ""))
            snippet = content[:200] + ("..." if len(content) > 200 else "")
            citations.append({
                "chunk_id": str(c.get("chunk_id")),
                "document_id": str(p.get("doc_id", "")),
                "filename": str(p.get("filename", "Document")),
                "page": int(p.get("page_number", 1)),
                "section": str(p.get("section", "General")),
                "snippet": snippet,
                "score": round(float(c.get("rerank_score", c.get("score", 0.0))), 3),
            })

        # 8. Voice TTS Synthesis (if requested)
        audio_b64 = None
        tts_ms = 0.0
        if audio_requested and answer:
            t5 = time.perf_counter()
            audio_b64 = await tts_provider.synthesize_base64(answer, language)
            tts_ms = round((time.perf_counter() - t5) * 1000, 2)
        latency_breakdown["tts_ms"] = tts_ms

        latency_breakdown["total_ms"] = round((time.perf_counter() - start_total) * 1000, 2)

        return {
            "answer": answer,
            "intent": intent,
            "retrieval_strategy": retrieval_strategy,
            "grounding_score": grounding_result["grounding_score"],
            "grounding_status": grounding_result["status"],
            "unsupported_claims": grounding_result.get("unsupported_claims", []),
            "citations": citations,
            "latency": latency_breakdown,
            "audio_base64": audio_b64,
        }


rag_pipeline = RAGPipeline()
