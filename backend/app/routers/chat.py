import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.retriever import retrieve
from app.memory import (
    get_short_memory, get_rolling_summary, get_user_profile,
    should_update_summary, save_rolling_summary, save_user_profile,
)
from app.database import add_message, get_recent_messages
from app.llm import chat_stream, generate_rolling_summary, update_user_profile

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat endpoint with SSE streaming."""
    question = req.message.strip()
    if not question:
        return {"error": "消息不能为空"}

    def generate():
        # 1. RAG retrieval
        yield "event: status\ndata: 正在检索相关数据...\n\n"
        source_context = retrieve(question)

        # 2. Gather memory
        short_memory = get_short_memory()
        rolling_summary = get_rolling_summary()
        user_profile = get_user_profile()

        # 3. Save user message
        add_message("user", question)

        # 4. Stream response
        yield "event: status\ndata: 正在生成回答...\n\n"
        full_response = []
        for chunk in chat_stream(question, short_memory, rolling_summary, user_profile, source_context):
            full_response.append(chunk)
            yield f"data: {json.dumps(chunk)}\n\n"

        # Signal end
        yield "data: [DONE]\n\n"

        # 5. Save assistant response
        assistant_text = "".join(full_response)
        add_message("assistant", assistant_text)

        # 6. Trigger memory updates if needed
        if should_update_summary():
            recent = get_recent_messages(limit=20)
            old_summary = get_rolling_summary()
            new_summary = generate_rolling_summary(recent, old_summary)
            save_rolling_summary(new_summary)

            msg_count = len(get_recent_messages(limit=1000))
            if msg_count > 0 and (msg_count // 2) % (7 * 3) == 0:
                new_profile = update_user_profile(get_user_profile(), new_summary)
                save_user_profile(new_profile)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/messages")
async def get_messages():
    """Get conversation history."""
    messages = get_recent_messages(limit=100)
    return {"messages": messages}
