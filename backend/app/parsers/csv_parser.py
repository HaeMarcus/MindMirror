import csv
import hashlib
import io
import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Column alias mapping: canonical_name -> list of known aliases
# Covers: 钱迹, 随手记, 微信支付, 支付宝, 挖财, 网易有钱, etc.
# ---------------------------------------------------------------------------
COLUMN_ALIASES: dict[str, list[str]] = {
    "时间": ["时间", "日期", "交易时间", "交易日期", "记账时间", "记账日期", "付款时间", "创建时间", "date", "time"],
    "分类": ["分类", "类别", "交易分类", "类型名称", "一级分类", "交易类型", "category"],
    "二级分类": ["二级分类", "子分类", "子类别", "细分类", "subcategory"],
    "类型": ["类型", "收支", "收支类型", "收/支", "收支方向", "收支分类", "type"],
    "金额": ["金额", "金额(元)", "金额（元）", "交易金额", "发生金额", "amount"],
    "币种": ["币种", "货币", "currency"],
    "备注": ["备注", "说明", "备注信息", "商品说明", "商品", "交易对方", "对方", "描述", "note", "remark", "description"],
    "标签": ["标签", "tag", "标记", "tags"],
}

# Only time + amount are truly required; everything else is optional
REQUIRED_CANONICAL = {"时间", "金额"}

# Type value normalization
INCOME_VALUES = {"收入", "入", "income", "收"}
EXPENSE_VALUES = {"支出", "出", "expense", "支"}


def _build_column_map(fieldnames: list[str]) -> dict[str, str]:
    """Map actual CSV column names to canonical names via alias matching.

    Returns dict: canonical_name -> actual_column_name
    """
    col_map: dict[str, str] = {}
    # Strip BOM and whitespace from field names
    cleaned = [f.lstrip("\ufeff").strip() for f in fieldnames]

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            alias_lower = alias.lower()
            for actual, cleaned_name in zip(fieldnames, cleaned):
                if cleaned_name.lower() == alias_lower and canonical not in col_map:
                    col_map[canonical] = actual
                    break
            if canonical in col_map:
                break

    return col_map


def _clean_amount(raw: str) -> float:
    """Parse amount string, handling ¥/￥ symbols, commas, +/- signs."""
    if not raw:
        return 0.0
    s = raw.strip()
    s = s.replace("¥", "").replace("￥", "").replace(",", "").replace(" ", "")
    # Handle parenthesized negatives like (100.00)
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def _infer_type(txn_type_raw: str, amount: float) -> str:
    """Normalize transaction type to '收入' or '支出'.

    Falls back to amount sign if type column is missing or unrecognized.
    """
    if txn_type_raw:
        t = txn_type_raw.strip().lower()
        if t in INCOME_VALUES:
            return "收入"
        if t in EXPENSE_VALUES:
            return "支出"
        # Some apps use "不计收支" or "转账" etc.
        if "收入" in txn_type_raw:
            return "收入"
        if "支出" in txn_type_raw:
            return "支出"
    # Infer from sign: negative = expense, positive = income
    if amount < 0:
        return "支出"
    elif amount > 0:
        return "收入"
    return ""


def parse_ledger_csv(content: str, source_name: str) -> dict:
    """Parse ledger CSV with flexible column matching.

    Supports: 钱迹, 随手记, 微信支付, 支付宝, and other common formats.
    """
    # Handle BOM
    if content.startswith("\ufeff"):
        content = content[1:]

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV 文件为空或无法解析表头")

    col_map = _build_column_map(list(reader.fieldnames))

    # Check required columns
    missing = REQUIRED_CANONICAL - set(col_map.keys())
    if missing:
        labels = {"时间": "时间/日期", "金额": "金额/amount"}
        missing_labels = [labels.get(m, m) for m in missing]
        raise ValueError(f"CSV 缺少必要列: {', '.join(missing_labels)}。检测到的列: {', '.join(reader.fieldnames)}")

    doc_id = _hash_id("ledger_csv", source_name, content[:200])
    chunks = []
    rows_data = []
    times = []

    def _get(row: dict, canonical: str, default: str = "") -> str:
        actual_col = col_map.get(canonical)
        if actual_col is None:
            return default
        return (row.get(actual_col) or "").strip()

    for i, row in enumerate(reader):
        time_str = _get(row, "时间")
        category = _get(row, "分类")
        sub_category = _get(row, "二级分类")
        txn_type_raw = _get(row, "类型")
        amount_raw = _get(row, "金额", "0")
        currency = _get(row, "币种", "CNY")
        note = _get(row, "备注")
        tag = _get(row, "标签")

        amount = _clean_amount(amount_raw)
        txn_type = _infer_type(txn_type_raw, amount)

        # Ensure amount is positive for downstream summaries
        amount_abs = abs(amount)

        if time_str:
            times.append(time_str)

        # If no category, try to use note as a fallback label
        if not category and note:
            category = "其他"

        # Build searchable text for each row
        cat_str = f"{category}/{sub_category}" if sub_category else category
        text = f"{time_str} {txn_type} {amount_abs}{currency} {cat_str}"
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
                "amount": str(amount_abs),
                "note": note,
            },
        })

        rows_data.append({
            "time": time_str,
            "category": category,
            "sub_category": sub_category,
            "type": txn_type,
            "amount": amount_abs,
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
        if not key:
            key = "未分类"
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
    """Normalize time string to YYYY-MM-DD HH:MM for correct sorting.

    Handles: 2025/12/31 15:53, 2025-12-31 15:53, 2025年12月31日 etc.
    """
    if not time_str:
        return ""
    # Replace Chinese date markers and common separators
    s = time_str.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").strip()
    parts = s.split(" ", 1)
    date_parts = parts[0].split("-")
    if len(date_parts) == 3:
        try:
            normalized_date = f"{date_parts[0]}-{int(date_parts[1]):02d}-{int(date_parts[2]):02d}"
        except ValueError:
            normalized_date = parts[0]
    elif len(date_parts) == 2:
        try:
            normalized_date = f"{date_parts[0]}-{int(date_parts[1]):02d}"
        except ValueError:
            normalized_date = parts[0]
    else:
        normalized_date = parts[0]
    return f"{normalized_date} {parts[1]}" if len(parts) > 1 else normalized_date


def _extract_month(time_str: str) -> str:
    """Extract YYYY-MM from time string like '2025/12/31 15:53' or '2025年12月31日'."""
    if not time_str:
        return ""
    s = time_str.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
    parts = s.split(" ")[0].split("-")
    if len(parts) >= 2:
        try:
            return f"{parts[0]}-{int(parts[1]):02d}"
        except ValueError:
            return ""
    return ""


def _hash_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
