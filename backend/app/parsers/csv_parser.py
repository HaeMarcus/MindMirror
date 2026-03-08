import csv
import hashlib
import io
from collections import defaultdict


CORE_COLUMNS = {"时间", "分类", "二级分类", "类型", "金额", "币种", "备注", "标签"}


def parse_ledger_csv(content: str, source_name: str) -> dict:
    """Parse 钱迹 CSV, return document + chunks (rows + summaries)."""
    reader = csv.DictReader(io.StringIO(content))
    actual_cols = set(reader.fieldnames or [])

    missing = CORE_COLUMNS - actual_cols
    if missing:
        raise ValueError(f"CSV 缺少核心列: {missing}")

    doc_id = _hash_id("ledger_csv", source_name, content[:200])
    chunks = []
    rows_data = []
    times = []

    for i, row in enumerate(reader):
        time_str = row.get("时间", "").strip()
        category = row.get("分类", "").strip()
        sub_category = row.get("二级分类", "").strip()
        txn_type = row.get("类型", "").strip()
        amount = row.get("金额", "0").strip()
        currency = row.get("币种", "CNY").strip()
        note = row.get("备注", "").strip()
        tag = row.get("标签", "").strip()

        if time_str:
            times.append(time_str)

        # Build searchable text for each row
        cat_str = f"{category}/{sub_category}" if sub_category else category
        text = f"{time_str} {txn_type} {amount}{currency} {cat_str}"
        if note:
            text += f" {note}"
        if tag:
            text += f" #{tag}"

        chunk_id = f"{doc_id}_row_{i}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "chunk_type": "ledger_row",
            "content": text,
            "metadata": {
                "source_type": "ledger_csv",
                "source_name": source_name,
                "date": time_str,
                "category": category,
                "sub_category": sub_category,
                "type": txn_type,
                "amount": amount,
                "note": note,
            },
        })

        rows_data.append({
            "time": time_str,
            "category": category,
            "sub_category": sub_category,
            "type": txn_type,
            "amount": float(amount) if amount else 0,
            "note": note,
        })

    # Generate summary chunks
    summary_chunks = _generate_summaries(doc_id, source_name, rows_data)
    chunks.extend(summary_chunks)

    # Normalize times for correct sorting (zero-pad month/day)
    normalized = sorted(set(_normalize_time(t) for t in times if t)) if times else []
    time_range_start = normalized[0] if normalized else None
    time_range_end = normalized[-1] if normalized else None

    document = {
        "doc_id": doc_id,
        "source_type": "ledger_csv",
        "source_name": source_name,
        "time_range_start": time_range_start,
        "time_range_end": time_range_end,
        "metadata": {
            "row_count": len(rows_data),
            "chunk_count": len(chunks),
        },
    }

    return {"document": document, "chunks": chunks}


def _generate_summaries(doc_id: str, source_name: str, rows: list[dict]) -> list[dict]:
    chunks = []

    # Monthly summaries
    monthly = defaultdict(lambda: {"income": 0, "expense": 0, "categories": defaultdict(float), "sub_categories": defaultdict(float), "items": []})
    for r in rows:
        month = _extract_month(r["time"])
        if not month:
            continue
        if r["type"] == "收入":
            monthly[month]["income"] += r["amount"]
        elif r["type"] == "支出":
            monthly[month]["expense"] += r["amount"]
            monthly[month]["categories"][r["category"]] += r["amount"]
            if r["sub_category"]:
                monthly[month]["sub_categories"][f"{r['category']}/{r['sub_category']}"] += r["amount"]
        monthly[month]["items"].append(r)

    for month, data in sorted(monthly.items()):
        year, mon = month.split("-")
        top_cats = sorted(data["categories"].items(), key=lambda x: -x[1])[:5]
        cats_detail = "、".join(f"{c}花费{a:.0f}元" for c, a in top_cats)
        balance = data["income"] - data["expense"]
        balance_desc = f"结余{balance:.0f}元" if balance >= 0 else f"超支{-balance:.0f}元"

        # Collect notable sub-categories for richer context
        top_subs = sorted(data["sub_categories"].items(), key=lambda x: -x[1])[:3]
        subs_detail = ""
        if top_subs:
            subs_detail = "。其中细分开销较大的是：" + "、".join(f"{s}({a:.0f}元)" for s, a in top_subs)

        text = (
            f"在{year}年{int(mon)}月，你的总收入为{data['income']:.0f}元，总支出为{data['expense']:.0f}元，{balance_desc}。"
            f"主要开销分布在：{cats_detail}{subs_detail}。"
            f"本月共有{len(data['items'])}笔交易记录。"
        )

        chunks.append({
            "chunk_id": f"{doc_id}_month_{month}",
            "doc_id": doc_id,
            "chunk_type": "ledger_month_summary",
            "content": text,
            "metadata": {
                "source_type": "ledger_csv",
                "source_name": source_name,
                "period": month,
                "income": data["income"],
                "expense": data["expense"],
            },
        })

    # Category summaries
    cat_totals = defaultdict(lambda: {"income": 0, "expense": 0, "count": 0, "notes": []})
    for r in rows:
        key = r["category"]
        if r["type"] == "收入":
            cat_totals[key]["income"] += r["amount"]
        elif r["type"] == "支出":
            cat_totals[key]["expense"] += r["amount"]
        cat_totals[key]["count"] += 1
        if r.get("note"):
            cat_totals[key]["notes"].append(r["note"])

    for cat, data in sorted(cat_totals.items(), key=lambda x: -(x[1]["income"] + x[1]["expense"])):
        parts = []
        if data["expense"]:
            parts.append(f"累计支出{data['expense']:.0f}元")
        if data["income"]:
            parts.append(f"累计收入{data['income']:.0f}元")
        amounts_str = "，".join(parts)

        # Include a few representative notes for semantic richness
        note_str = ""
        unique_notes = list(dict.fromkeys(n for n in data["notes"] if n))[:5]
        if unique_notes:
            note_str = f"，常见备注包括：{'、'.join(unique_notes)}"

        text = f"在你的所有账单记录中，「{cat}」类别共有{data['count']}笔交易，{amounts_str}{note_str}。"

        chunks.append({
            "chunk_id": f"{doc_id}_cat_{hashlib.md5(cat.encode()).hexdigest()[:8]}",
            "doc_id": doc_id,
            "chunk_type": "ledger_category_summary",
            "content": text,
            "metadata": {
                "source_type": "ledger_csv",
                "source_name": source_name,
                "category": cat,
                "total": data["income"] + data["expense"],
            },
        })

    # Overall summary for the entire CSV
    if rows:
        total_income = sum(r["amount"] for r in rows if r["type"] == "收入")
        total_expense = sum(r["amount"] for r in rows if r["type"] == "支出")
        months_sorted = sorted(monthly.keys())
        period_str = f"{months_sorted[0]}至{months_sorted[-1]}" if len(months_sorted) > 1 else months_sorted[0] if months_sorted else "未知时段"
        top_all_cats = sorted(
            ((cat, d["expense"]) for cat, d in cat_totals.items() if d["expense"] > 0),
            key=lambda x: -x[1]
        )[:5]
        top_cats_str = "、".join(f"{c}({a:.0f}元)" for c, a in top_all_cats)
        text = (
            f"这份账单涵盖了{period_str}期间的财务记录，共{len(rows)}笔交易。"
            f"期间总收入{total_income:.0f}元，总支出{total_expense:.0f}元。"
            f"支出最多的类别依次为：{top_cats_str}。"
        )
        chunks.append({
            "chunk_id": f"{doc_id}_overall",
            "doc_id": doc_id,
            "chunk_type": "ledger_overall_summary",
            "content": text,
            "metadata": {
                "source_type": "ledger_csv",
                "source_name": source_name,
                "period": period_str,
                "total_income": total_income,
                "total_expense": total_expense,
            },
        })

    return chunks


def _normalize_time(time_str: str) -> str:
    """Normalize time string to YYYY-MM-DD HH:MM for correct sorting."""
    if not time_str:
        return ""
    parts = time_str.replace("/", "-").split(" ")
    date_parts = parts[0].split("-")
    if len(date_parts) == 3:
        normalized_date = f"{date_parts[0]}-{int(date_parts[1]):02d}-{int(date_parts[2]):02d}"
    elif len(date_parts) == 2:
        normalized_date = f"{date_parts[0]}-{int(date_parts[1]):02d}"
    else:
        normalized_date = parts[0]
    return f"{normalized_date} {parts[1]}" if len(parts) > 1 else normalized_date


def _extract_month(time_str: str) -> str:
    """Extract YYYY-MM from time string like '2025/12/31 15:53'."""
    if not time_str:
        return ""
    parts = time_str.replace("/", "-").split(" ")[0].split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{int(parts[1]):02d}"
    return ""


def _hash_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
