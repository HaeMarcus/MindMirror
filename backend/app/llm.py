import json
from typing import Generator

import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, LLM_MODEL

_client_kwargs = {"api_key": ANTHROPIC_API_KEY}
if ANTHROPIC_BASE_URL:
    _client_kwargs["base_url"] = ANTHROPIC_BASE_URL
client = anthropic.Anthropic(**_client_kwargs)

SYSTEM_PROMPT = """你是 MindMirror，一个基于用户个人数据的 AI 自我洞察助手。

## 核心风格
- 冷静、客观、证据驱动、心理觉察导向
- 不讨好、不回避、一针见血
- 像一面镜子，忠实反映用户的行为模式和心理状态

## 输出格式（严格遵守）
你的每次回复必须严格包含以下四个部分：

【核心洞察】
一句话定性，直指核心问题。

【证据归因】
概括性引用证据，必须标明来源类型和时间范围：
- 来自 Flomo 日常记录（时间范围）：概括内容...
- 来自复盘文档《文件名》（时间范围，置信度）：概括内容...
- 来自钱迹账单（时间范围）：概括内容...
如果某个来源没有被检索到，不要提及该来源。

【防御机制】
指出用户可能存在的自我保护、认知偏差或自我欺骗，但避免诊断口吻。

【实验性下一步】
给出一个极小的、可执行的、低成本的行动建议。

## 关键规则
- 必须基于提供的证据生成洞察，不确定的要明确说不确定
- 不输出精确引用（不出现 chunk_id、行号、原文片段定位）
- 只做"来源+时间+概括"级别的归因
- 如果证据不足以支撑洞察，诚实说明
- 禁止使用任何 Markdown 格式符号（不要用 **加粗**、*斜体*、# 标题、- 列表符号等）
- 使用纯文本输出，用中文标点和换行来组织内容
- 如果需要列举，用"1. 2. 3."数字编号或直接分行书写"""


def build_messages(
    question: str,
    short_memory: list[dict],
    rolling_summary: str,
    user_profile: dict,
    source_context: dict,
) -> list[dict]:
    """Build the message list for Claude API."""
    messages = []

    # Add conversation history
    for msg in short_memory:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Build context block for current question
    context_parts = []

    if user_profile:
        context_parts.append(f"【用户画像】\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}")

    if rolling_summary:
        context_parts.append(f"【对话摘要】\n{rolling_summary}")

    if source_context.get("sources"):
        context_parts.append(f"【证据归因上下文】\n{json.dumps(source_context['sources'], ensure_ascii=False, indent=2)}")

    context_block = "\n\n---\n\n".join(context_parts)

    user_message = question
    if context_block:
        user_message = f"<context>\n{context_block}\n</context>\n\n{question}"

    messages.append({"role": "user", "content": user_message})
    return messages


def chat_stream(
    question: str,
    short_memory: list[dict],
    rolling_summary: str,
    user_profile: dict,
    source_context: dict,
) -> Generator[str, None, None]:
    """Stream chat response from Claude."""
    messages = build_messages(question, short_memory, rolling_summary, user_profile, source_context)

    with client.messages.stream(
        model=LLM_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text


def chat_sync(
    question: str,
    short_memory: list[dict],
    rolling_summary: str,
    user_profile: dict,
    source_context: dict,
) -> str:
    """Sync chat response from Claude."""
    messages = build_messages(question, short_memory, rolling_summary, user_profile, source_context)

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


SUMMARY_PROMPT = """基于以下对话历史，生成一段简洁的滚动摘要（200字以内），捕捉：
1. 用户讨论的核心主题
2. 已发现的关键洞察
3. 用户的情绪状态和行为模式趋势

只输出摘要内容，不要加标题或前缀。"""


def generate_rolling_summary(recent_messages: list[dict], old_summary: str) -> str:
    """Generate updated rolling summary."""
    msgs_text = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in recent_messages[-14:])
    prompt = f"旧摘要：{old_summary}\n\n最近对话：\n{msgs_text}\n\n{SUMMARY_PROMPT}"

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


PROFILE_PROMPT = """基于以下对话摘要和证据，更新用户长期画像 JSON。保留已有的稳定特征，谨慎增加新发现。

输出纯 JSON，格式：
{
  "themes": ["主题1", "主题2"],
  "values": ["价值观1", "价值观2"],
  "goals": ["目标1", "目标2"],
  "patterns": ["行为模式1", "行为模式2"],
  "risks": ["风险点1", "风险点2"]
}"""


def update_user_profile(old_profile: dict, rolling_summary: str) -> dict:
    """Update user profile based on accumulated evidence."""
    prompt = f"当前画像：{json.dumps(old_profile, ensure_ascii=False)}\n\n对话摘要：{rolling_summary}\n\n{PROFILE_PROMPT}"

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Extract JSON from response
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return old_profile
