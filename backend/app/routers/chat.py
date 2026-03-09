import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.retriever import retrieve
from app.memory import (
    get_short_memory, get_rolling_summary, get_user_profile,
    should_update_summary, mark_summary_updated, save_rolling_summary,
    should_update_profile, mark_profile_updated, save_user_profile,
)
from app.database import (
    add_message, get_recent_messages, clear_all_data,
    add_feedback, get_feedback_stats, get_feedback_analytics,
    create_user, user_exists,
)
from app.llm import chat_stream, generate_rolling_summary, update_user_profile
from app.config import APP_VERSION

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    nickname: str


class RegisterRequest(BaseModel):
    nickname: str


class FeedbackRequest(BaseModel):
    message_id: int
    rating: str  # "accurate" or "inaccurate"
    nickname: str = ""
    source_types: str = ""  # comma-separated, e.g. "flomo_html,ledger_csv"


# ---- User registration ----

@router.post("/register")
async def register(req: RegisterRequest):
    nickname = req.nickname.strip()
    if not nickname:
        return {"error": "昵称不能为空"}
    if user_exists(nickname):
        return {"error": "该昵称已被使用，请换一个", "exists": True}
    create_user(nickname)
    return {"status": "ok", "nickname": nickname}


@router.get("/check-nickname")
async def check_nickname(nickname: str = Query(...)):
    return {"exists": user_exists(nickname.strip())}


# ---- Chat ----

@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat endpoint with SSE streaming."""
    question = req.message.strip()
    user_id = req.nickname.strip()
    if not question:
        return {"error": "消息不能为空"}

    def generate():
        import traceback
        try:
            # 1. RAG retrieval
            yield "event: status\ndata: 正在检索相关数据...\n\n"
            source_context = retrieve(question, user_id=user_id)

            # 2. Gather memory
            short_memory = get_short_memory(user_id=user_id)
            rolling_summary = get_rolling_summary(user_id=user_id)
            user_profile = get_user_profile(user_id=user_id)

            # 3. Save user message
            add_message("user", question, user_id=user_id)

            # 4. Stream response
            yield "event: status\ndata: 正在生成回答...\n\n"
            full_response = []
            for chunk in chat_stream(question, short_memory, rolling_summary, user_profile, source_context):
                full_response.append(chunk)
                yield f"data: {json.dumps(chunk)}\n\n"

            # 5. Save assistant response
            assistant_text = "".join(full_response)
            msg_id = add_message("assistant", assistant_text, user_id=user_id)

            # Signal end with message_id and source_types for feedback tracking
            used_sources = ",".join(sorted({s["source_type"] for s in source_context.get("sources", [])}))
            yield f"event: done\ndata: {json.dumps({'message_id': msg_id, 'source_types': used_sources})}\n\n"

            # 6. Trigger memory updates (counter-based, independent triggers)
            if should_update_summary(user_id=user_id):
                recent = get_recent_messages(limit=20, user_id=user_id)
                old_summary = get_rolling_summary(user_id=user_id)
                new_summary = generate_rolling_summary(recent, old_summary)
                save_rolling_summary(new_summary, user_id=user_id)
                mark_summary_updated(user_id=user_id)

            if should_update_profile(user_id=user_id):
                summary = get_rolling_summary(user_id=user_id)
                if summary:
                    new_profile = update_user_profile(get_user_profile(user_id=user_id), summary)
                    save_user_profile(new_profile, user_id=user_id)
                mark_profile_updated(user_id=user_id)

        except Exception as e:
            traceback.print_exc()
            error_msg = f"服务器内部错误：{type(e).__name__}: {e}"
            yield f"event: error\ndata: {json.dumps(error_msg)}\n\n"
            yield f"event: done\ndata: {json.dumps({'message_id': None, 'source_types': ''})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/messages")
async def get_messages(nickname: str = Query(...)):
    """Get conversation history for a user."""
    messages = get_recent_messages(limit=100, user_id=nickname.strip())
    return {"messages": messages}


@router.delete("/reset")
async def reset_all(nickname: str = Query(...)):
    """Clear all data for a specific user. FAISS orphans are harmless."""
    clear_all_data(user_id=nickname.strip())
    return {"status": "ok", "message": "所有数据已清除"}


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Record user feedback on assistant response accuracy."""
    if req.rating not in ("accurate", "inaccurate"):
        return {"error": "rating must be 'accurate' or 'inaccurate'"}
    add_feedback(req.message_id, req.rating, user_id=req.nickname,
                 app_version=APP_VERSION, source_types=req.source_types)
    return {"status": "ok"}


@router.get("/feedback/stats")
async def feedback_stats():
    """Get basic feedback statistics."""
    return get_feedback_stats()


@router.get("/profile")
async def get_profile(nickname: str = Query(...)):
    """Get user profile including big_five scores."""
    profile = get_user_profile(user_id=nickname.strip())
    return {"profile": profile}


@router.get("/analytics")
async def analytics(days: int = Query(default=30)):
    """Developer analytics dashboard data."""
    return get_feedback_analytics(days=days)
