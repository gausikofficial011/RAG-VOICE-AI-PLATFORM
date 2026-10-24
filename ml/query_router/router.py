"""
Model B — Intelligent Query Router
Routes incoming queries based on intent classification, conversational context, and safety boundaries.
"""

from typing import Dict, Any, Optional
from ml.intent_classifier.predict import intent_classifier


class QueryRouter:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def route(
        self,
        query: str,
        has_active_kb: bool = True,
        has_history: bool = False,
    ) -> Dict[str, Any]:
        """
        Route query to optimal processing destination.
        Returns: {
            "route": "RAG" | "DIRECT_RESPONSE" | "CONVERSATION_MEMORY" | "CLARIFICATION" | "SAFETY_REFUSAL",
            "intent": str,
            "confidence": float,
            "requires_retrieval": bool,
            "requires_memory": bool,
            "reasoning": str
        }
        """
        classification = intent_classifier.predict(query)
        intent = classification["intent"]
        confidence = classification["confidence"]

        # 1. Safety & Refusal (High priority security guardrail)
        hazardous_terms = ["bomb", "explosive", "weapon", "hack", "malware", "stolen", "poison", "illegal"]
        if any(h in query.lower() for h in hazardous_terms) or (intent == "OUT_OF_SCOPE" and confidence >= 0.25):
            return {
                "route": "SAFETY_REFUSAL",
                "intent": "OUT_OF_SCOPE",
                "confidence": max(confidence, 0.95),
                "requires_retrieval": False,
                "requires_memory": False,
                "reasoning": "Query triggers safety boundaries or out-of-scope compliance policies.",
            }

        # Check if query is conversational greeting / small talk
        q_clean = query.lower().strip("?!. ,")
        words = q_clean.split()
        greeting_vocab = {
            "hi", "hello", "hey", "howdy", "greetings",
            "how", "are", "you", "doing", "fine", "good", "morning", "afternoon",
            "evening", "there", "whats", "what's", "up", "thanks", "thank"
        }
        is_conversational_greeting = (
            (len(words) > 0 and all(w in greeting_vocab for w in words))
            or (intent == "GREETING" and not any(w in q_clean for w in ["document", "policy", "refund", "report", "directive", "file", "table", "data", "figure", "temperature"]))
        )

        # Check if query is clearly an interrogative question
        is_question = (
            (any(query.lower().startswith(w) for w in ["what", "how", "when", "where", "why", "who", "which", "and how", "can you", "is there"]) or "?" in query)
            and not is_conversational_greeting
        )

        # 2. Greetings & Salutations (requires high confidence and not an interrogative question)
        if is_conversational_greeting or (intent == "GREETING" and confidence >= 0.5 and not is_question):
            return {
                "route": "DIRECT_RESPONSE",
                "intent": "GREETING",
                "confidence": max(float(confidence), 0.95),
                "requires_retrieval": False,
                "requires_memory": False,
                "reasoning": "Conversational greeting does not require knowledge base retrieval.",
            }

        # 2b. PC / Laptop Workflow Agent Action Check
        agent_action_keywords = [
            "cpu", "ram", "memory", "battery", "hardware", "specs", "system status",
            "pc status", "laptop status", "health check", "running apps", "processes",
            "task manager", "open google", "open browser", "open notepad", "open calc",
            "open calculator", "launch", "search file", "find file", "clean cache",
            "cleanup", "generate report", "create report", "system report", "workflow"
        ]
        is_agent_action = any(k in q_clean for k in agent_action_keywords) or (
            q_clean.startswith("open ") and len(q_clean.split()) <= 4 and not any(w in q_clean for w in ["policy", "directive", "document", "contract"])
        )
        if is_agent_action:
            return {
                "route": "PC_AGENT",
                "intent": "PC_AGENT_ACTION",
                "confidence": 0.98,
                "requires_retrieval": False,
                "requires_memory": False,
                "reasoning": "Query triggers autonomous PC and laptop agent workflow automation.",
            }

        # 3. Follow-up queries needing conversation memory
        if intent == "FOLLOW_UP":
            return {
                "route": "CONVERSATION_MEMORY",
                "intent": intent,
                "confidence": confidence,
                "requires_retrieval": has_active_kb,
                "requires_memory": True,
                "reasoning": "Query references prior conversational context.",
            }

        # 4. Clarification requests
        if intent == "CLARIFICATION":
            return {
                "route": "CLARIFICATION",
                "intent": intent,
                "confidence": confidence,
                "requires_retrieval": False,
                "requires_memory": True,
                "reasoning": "User requests clarification on earlier assistant output.",
            }

        # 5. Low confidence query needing clarification or fallback
        if confidence < self.confidence_threshold and not has_active_kb:
            return {
                "route": "CLARIFICATION",
                "intent": intent,
                "confidence": confidence,
                "requires_retrieval": False,
                "requires_memory": False,
                "reasoning": "Low intent confidence and no active knowledge base selected.",
            }

        # 6. Default to RAG for document queries, summarizations, facts, comparisons
        return {
            "route": "RAG" if has_active_kb else "DIRECT_RESPONSE",
            "intent": intent,
            "confidence": confidence,
            "requires_retrieval": has_active_kb,
            "requires_memory": has_history,
            "reasoning": "Query requires factual retrieval against private knowledge base." if has_active_kb else "General knowledge query.",
        }


query_router = QueryRouter()
