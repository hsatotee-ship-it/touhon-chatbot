import logging
import traceback
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.schemas import ChatMessageResponse, ChatRequest, ChatResponse, ChatSessionResponse
from app.models.tables import ChatMessage, ChatSession, User
from app.services.chat import generate_answer
from app.services.vector_search import search_similar_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        # Get or create session
        if body.session_id:
            session = await db.get(ChatSession, body.session_id)
            if not session or session.user_id != user.id:
                raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        else:
            session = ChatSession(user_id=user.id, title=body.message[:50])
            db.add(session)
            await db.flush()

        # Search similar chunks
        logger.info(f"Searching chunks for user={user.id}")
        chunks = await search_similar_chunks(db, body.message, user.id, top_k=5)
        logger.info(f"Found {len(chunks)} chunks")

        # Get chat history
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
        )
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_result.scalars().all()
        ]

        # Generate answer
        logger.info("Calling generate_answer")
        answer, sources = generate_answer(body.message, chunks, history)
        logger.info("generate_answer completed")

        # Save messages
        user_msg = ChatMessage(session_id=session.id, role="user", content=body.message)
        assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=answer, sources=sources)
        db.add_all([user_msg, assistant_msg])
        await db.commit()

        return ChatResponse(answer=answer, sources=sources, session_id=session.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {type(e).__name__}: {e}")


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            ChatSession,
            func.count(ChatMessage.id).label("message_count"),
        )
        .outerjoin(ChatMessage)
        .where(ChatSession.user_id == user.id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = []
    for row in result.all():
        s = ChatSessionResponse.model_validate(row[0])
        s.message_count = row[1]
        sessions.append(s)
    return sessions


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return [ChatMessageResponse.model_validate(m) for m in result.scalars().all()]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    await db.delete(session)
    await db.commit()
