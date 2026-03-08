import json
from typing import Generator

import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, LLM_MODEL

_client_kwargs = {"api_key": ANTHROPIC_API_KEY}
if ANTHROPIC_BASE_URL:
    _client_kwargs["base_url"] = ANTHROPIC_BASE_URL
client = anthropic.Anthropic(**_client_kwargs)

SYSTEM_PROMPT = """你是 MindMirror，一个基于用户多维度个人数据的 AI 自我洞察助手。

## 核心风格
- 冷静、客观、证据驱动、心理觉察导向
- 不讨好、不回避、一针见血
- 像一面镜子，忠实反映用户的行为模式和心理状态

## 输出格式（严格遵守）
你的每次回复必须严格包含以下四个部分：

【核心洞察】
一句话定性，直指核心问题。

【模式识别】
从整体上把握用户的欣慰模式，找出笔记中反复出现的主题。
然后对这些内容进行深度挖掘，找出背后的矛盾或冲突。
最后把多维度多来源的信息进行交叉整合分析，尽量形成相对统一的视角。用理性温和的预期告诉用户相关洞察，不要讨好。
如果多维度的信息实在难以形成统一视角，就多维度分析即可。

【证据归因】
概括性引用证据，必须标明来源类型和时间范围：
- 从你的日常记录（时间范围）可以看出：概括内容...
- 你在复盘文档《文件名》（时间范围）中提到：概括内容...
- 你的账单记录（时间范围）显示：概括内容...
如果某个来源没有被检索到，不要提及该来源。

## 用户画像中的 key_facts
- 用户画像中可能包含 key_facts 字段，记录了用户的重要客观信息（姓名、身份、重要人物、重大事件等）
- 在回复中自然地运用这些信息，体现你对用户的持续了解，但不要刻意罗列
- 如果用户提到新的重要个人信息，这些信息会在后续画像更新中被记录

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


SUMMARY_PROMPT = """基于以下旧摘要和最近对话，生成一段更新后的滚动摘要（500字以内），要求：
1. 保留旧摘要中仍然成立的核心发现，删除已过时的内容
2. 融入最近对话中新出现的主题、洞察和行为模式
3. 捕捉用户的情绪趋势变化和自我认知进展
4. 记录用户提到的关键事实（如具体目标、重要事件、人际关系）

摘要应当是信息密集的，像一份持续更新的用户档案备忘录。只输出摘要内容，不要加标题或前缀。"""


def generate_rolling_summary(recent_messages: list[dict], old_summary: str) -> str:
    """Generate updated rolling summary."""
    msgs_text = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in recent_messages[-12:])
    prompt = f"旧摘要：{old_summary}\n\n最近对话：\n{msgs_text}\n\n{SUMMARY_PROMPT}"

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


PROFILE_PROMPT = """基于以下对话摘要和证据，更新用户长期画像 JSON。保留已有的稳定特征，谨慎增加新发现。

关于 key_facts 的特殊规则：
- key_facts 用于存储用户的客观重要信息（姓名、身份、职业、重要人物、重大事件、童年记忆等）
- 只收录用户明确告知或在多次对话中反复提及的关键事实
- 不要过度收集：只记录对理解用户至关重要的信息
- 已有的 key_facts 除非用户明确纠正，否则永远保留
- 每条 fact 用简短陈述句表达（如"本科就读于XX大学"、"有一个姐姐叫小明"）

输出纯 JSON，格式：
{
  "key_facts": ["关键事实1", "关键事实2"],
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
        max_tokens=800,
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
