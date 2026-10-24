"""
RAG Query & Conversation API Router
Provides multi-turn conversational memory, hybrid retrieval, citations, and human feedback.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation, Message
from backend.app.models.feedback import UserFeedback
from backend.app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    FeedbackCreateRequest,
)
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.rag.pipeline import rag_pipeline
from backend.app.audit.service import audit_service

router = APIRouter(prefix="/rag", tags=["RAG Intelligence"])


@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_base(
    data: RAGQueryRequest,
    current_user: User = Depends(require_permission(Permission.CONV_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Ask a question through hybrid RAG with citations, grounding, and optional voice audio."""
    # 1. Manage Conversation Context
    conv = None
    if data.conversation_id:
        stmt = select(Conversation).where(
            Conversation.id == data.conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
        )
        res = await db.execute(stmt)
        conv = res.scalar_one_or_none()

    if not conv:
        # Create new conversation
        conv = Conversation(
            tenant_id=current_user.tenant_id,
            kb_id=data.kb_id,
            user_id=current_user.id,
            title=data.query[:40] + ("..." if len(data.query) > 40 else ""),
        )
        db.add(conv)
        await db.flush()

    # 2. Fetch recent conversation turns for context
    stmt_history = select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).limit(6)
    history_res = await db.execute(stmt_history)
    history_messages = list(reversed(history_res.scalars().all()))
    history_dicts = [{"role": m.role, "content": m.content} for m in history_messages]

    # 3. Save User Message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=data.query,
    )
    db.add(user_msg)
    await db.flush()

    # 4. Execute RAG Pipeline
    result = await rag_pipeline.execute(
        tenant_id=current_user.tenant_id,
        query=data.query,
        kb_id=data.kb_id or conv.kb_id,
        conversation_history=history_dicts,
        audio_requested=data.audio_requested,
        language=data.language or "en",
    )

    # 5. Save Assistant Message with Provenance & Metrics
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=result["answer"],
        intent=result["intent"],
        retrieval_strategy=result["retrieval_strategy"],
        grounding_score=result["grounding_score"],
        grounding_status=result["grounding_status"],
        citations=result["citations"],
        latency_metrics=result["latency"],
    )
    db.add(assistant_msg)
    await db.commit()

    return RAGQueryResponse(
        answer=result["answer"],
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        intent=result["intent"],
        retrieval_strategy=result["retrieval_strategy"],
        grounding_score=result["grounding_score"],
        grounding_status=result["grounding_status"],
        citations=result["citations"],
        latency=result["latency"],
        audio_base64=result.get("audio_base64"),
    )


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(require_permission(Permission.CONV_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List recent conversations for current user."""
    stmt = (
        select(Conversation)
        .where(
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id,
        )
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    convs = res.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "kb_id": c.kb_id,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in convs
    ]


@router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: str,
    current_user: User = Depends(require_permission(Permission.CONV_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full message history with citations and latency for a conversation."""
    stmt_conv = select(Conversation).where(
        Conversation.id == conv_id,
        Conversation.tenant_id == current_user.tenant_id,
    )
    conv = (await db.execute(stmt_conv)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    stmt_msgs = select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
    res = await db.execute(stmt_msgs)
    msgs = res.scalars().all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "citations": m.citations,
            "grounding_score": m.grounding_score,
            "grounding_status": m.grounding_status,
            "latency": m.latency_metrics,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: str,
    current_user: User = Depends(require_permission(Permission.CONV_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    stmt = select(Conversation).where(
        Conversation.id == conv_id,
        Conversation.tenant_id == current_user.tenant_id,
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    await db.delete(conv)
    await db.commit()
    return {"success": True, "message": "Conversation deleted."}


@router.post("/feedback")
async def submit_feedback(
    data: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit user feedback (thumbs up/down) for model quality evaluation."""
    stmt = select(Message).where(Message.id == data.message_id)
    msg = (await db.execute(stmt)).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Target message not found.")

    feedback = UserFeedback(
        tenant_id=current_user.tenant_id,
        message_id=data.message_id,
        user_id=current_user.id,
        rating=data.rating,
        feedback_type=data.feedback_type,
        comment=data.comment,
    )
    db.add(feedback)
    await db.commit()
    return {"success": True, "message": "Feedback recorded."}
