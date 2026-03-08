import json
import re
from collections import defaultdict

from app.embedding import encode, search
from app.database import get_chunks_by_faiss_ids
from app.config import FAISS_TOP_K, MAX_CONTEXT_TOKENS


# Keywords for source-aware reranking
CSV_KEYWORDS = {"消费", "支出", "收入", "账单", "花费", "预算", "房租", "工资", "理财", "记账", "金额", "结余", "财务"}
MD_KEYWORDS = {"复盘", "总结", "目标", "计划", "项目", "反思", "回顾", "成长", "学习", "职业", "年度", "长期"}
HTML_KEYWORDS = {"情绪", "感受", "心情", "关系", "焦虑", "开心", "难过", "习惯", "日常", "最近", "今天", "状态"}


def retrieve(query: str, user_id: str, top_k: int = FAISS_TOP_K) -> dict:
    """Full RAG pipeline: embed → search → rerank → compress → build context."""
    # 1. Encode query
    query_vec = encode([query])

    # 2. FAISS search (per-user index)
    raw_results = search(query_vec, user_id=user_id, top_k=top_k)
    if not raw_results:
        return {"sources": [], "raw_chunks": []}

    faiss_ids = [r[0] for r in raw_results]
    scores = {r[0]: r[1] for r in raw_results}

    # 3. Fetch chunk metadata (filtered by user_id)
    chunks = get_chunks_by_faiss_ids(faiss_ids, user_id=user_id)
    for c in chunks:
        c["score"] = scores.get(c["faiss_id"], 0)
        if c["metadata"]:
            c["metadata"] = json.loads(c["metadata"]) if isinstance(c["metadata"], str) else c["metadata"]

    # 4. Source-aware rerank
    chunks = _source_aware_rerank(query, chunks)

    # 5. Compress and build context
    context = _build_source_attribution_context(chunks)

    return context


def _source_aware_rerank(query: str, chunks: list[dict]) -> list[dict]:
    """Boost scores based on query-source relevance."""
    query_lower = query.lower()

    csv_boost = any(kw in query_lower for kw in CSV_KEYWORDS)
    md_boost = any(kw in query_lower for kw in MD_KEYWORDS)
    html_boost = any(kw in query_lower for kw in HTML_KEYWORDS)

    for c in chunks:
        meta = c.get("metadata", {})
        source_type = meta.get("source_type", "")
        boost = 1.0

        if csv_boost and source_type == "ledger_csv":
            boost = 1.3
        elif md_boost and source_type == "review_md":
            boost = 1.3
        elif html_boost and source_type == "flomo_html":
            boost = 1.3

        # Boost summary chunks slightly
        if c.get("chunk_type", "").endswith("_summary"):
            boost *= 1.1

        c["adjusted_score"] = c["score"] * boost

    chunks.sort(key=lambda x: x["adjusted_score"], reverse=True)
    return chunks


def _build_source_attribution_context(chunks: list[dict]) -> dict:
    """Build source_attribution_context JSON for LLM."""
    # Group by source
    source_groups = defaultdict(list)
    for c in chunks:
        meta = c.get("metadata", {})
        source_type = meta.get("source_type", "unknown")
        source_groups[source_type].append(c)

    sources = []
    total_tokens = 0

    for source_type, group_chunks in source_groups.items():
        if total_tokens >= MAX_CONTEXT_TOKENS:
            break

        # Deduplicate similar content
        seen_content = set()
        unique_chunks = []
        for c in group_chunks:
            content_key = c["content"][:100]
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_chunks.append(c)

        bullets = []
        source_name = ""
        time_range = None
        dates = []

        for c in unique_chunks[:5]:  # Max 5 per source
            meta = c.get("metadata", {})
            source_name = meta.get("source_name", "")
            date = meta.get("date") or meta.get("period") or meta.get("time_range")
            if date:
                dates.append(str(date))

            # Truncate content for bullet
            content = c["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            bullets.append(content)
            total_tokens += len(content)

        if dates:
            time_range = f"{min(dates)}~{max(dates)}" if len(dates) > 1 else dates[0]

        confidence = "high" if source_type == "ledger_csv" else "medium"
        if source_type == "review_md":
            meta0 = group_chunks[0].get("metadata", {}) if group_chunks else {}
            tc = meta0.get("time_confidence")
            if tc:
                confidence = tc

        sources.append({
            "source_type": source_type,
            "source_name": source_name,
            "time_range": time_range,
            "confidence": confidence,
            "summary_bullets": bullets,
        })

    return {
        "sources": sources,
        "raw_chunks": [{"content": c["content"], "metadata": c.get("metadata", {})} for c in chunks[:10]],
    }
