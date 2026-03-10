# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

MindMirror — AI self-awareness assistant that cross-references multi-source personal data (Flomo notes, Markdown reviews, CSV financial records) via RAG to surface behavioral patterns and cognitive blind spots. Chinese-language product with a "cold mirror" personality — evidence-driven, non-pleasing.

Live at https://mind-mirror-liart.vercel.app/ (Vercel frontend + Railway backend).

## Development Commands

### Frontend (`frontend/`)
```bash
cd frontend
pnpm install          # install dependencies
pnpm dev              # dev server on localhost:3000
pnpm build            # production build
pnpm lint             # ESLint via Next.js
```

### Backend (`backend/`)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```
Note: uvicorn must run from `backend/` since it imports `app.main` as a relative module path.

No automated test suite exists. Quality is verified manually via the dev servers.

## Architecture

**Frontend:** Next.js 15 + React 19 + Tailwind 4. Single-page chat UI. All API calls go through `frontend/lib/api.ts` using fetch + SSE streaming. State lives in React hooks + localStorage (keyed `mm_nickname`, `mm_sidebar`). The `next.config.ts` rewrites `/api/*` to the backend URL.

**Backend:** FastAPI + SQLite + FAISS. Entry point is `backend/app/main.py`. Two routers under `/api`: `ingest.py` (file upload with SSE progress) and `chat.py` (register, chat, feedback, analytics). All config constants live in `backend/app/config.py`.

### Frontend Component Hierarchy
`page.tsx` renders `ChatWindow` (the main orchestrator), which composes:
- `NicknamePrompt` — first-visit registration modal
- `Sidebar` — navigation, upload/data triggers, reset
- `MessageBubble` — individual chat messages with section-aware rendering
- `UploadPanel` / `DataPanel` — modal overlays for file upload and document management
- `RadarChart` — Big Five personality visualization (SVG)

### Data Flow

1. **Ingest:** User uploads file → parser (`parsers/flomo_parser.py`, `md_parser.py`, `csv_parser.py`) extracts chunks → embedded via bge-small-zh-v1.5 (512-dim) → stored in per-user FAISS index + SQLite
2. **Chat:** User message → retriever searches FAISS (top 12) → source-aware rerank (keyword-based boost, 1.3x for matching source type) → compress → build context with memory layers → Claude generates structured response via streaming

### Three-Layer Memory System (`memory.py`)
- **Short-term (Working Memory):** Last 3 rounds sent directly in LLM messages
- **Mid-term (Episodic Memory):** Rolling summary, updated every 5 rounds (and on first round), 500-char target
- **Long-term (Semantic Memory):** User profile JSON with key_facts, themes, values, goals, patterns, risks, big_five — updated every 10 rounds (and on first round)

### Source Types
Three canonical source type strings used throughout the codebase:
- `flomo_html` — daily notes/emotions (HTML export from Flomo)
- `review_md` — self-review/reflection documents (Markdown)
- `ledger_csv` — financial records (CSV export from 钱迹)

CSV rows are NOT vectorized — only monthly/category/overall summaries go into FAISS.

### API Endpoints
All under `/api` prefix:
- `POST /register` — create user by nickname
- `GET /check-nickname` — check if nickname exists
- `POST /ingest` — file upload (multipart form, SSE progress)
- `GET /documents` — list user's uploaded documents
- `POST /chat` — chat with SSE streaming
- `GET /messages` — conversation history
- `DELETE /reset` — clear all user data
- `POST /feedback` — submit accuracy rating
- `GET /feedback/stats` — basic feedback counts
- `GET /profile` — user profile + big_five scores
- `GET /analytics` — developer dashboard data
- `GET /health` — health check

### SSE Streaming Protocols
The two SSE endpoints use different formats:
- **Ingest** (`/api/ingest`): `data: {json}\n\n` with `type` field (`progress`, `done`)
- **Chat** (`/api/chat`): Named SSE events — `event: status`, `event: done`, `event: error`, plus bare `data:` lines for streamed text chunks

### Database Schema (SQLite)
Six tables: `users`, `documents`, `chunks`, `messages`, `memory`, `feedback`. Auto-migrations run on startup in `database.py` (adds columns for multi-user support). The `memory` table stores rolling summaries and user profiles as key-value pairs with composite `(user_id, key)` primary key.

## Environment Variables

**Backend `.env`:** `ANTHROPIC_API_KEY` (required), `ANTHROPIC_BASE_URL` (optional proxy), `CORS_ORIGIN` (optional extra origin), `DATA_DIR` (default: `backend/data`)

**Frontend `.env.local`:** `BACKEND_URL` (default: `http://localhost:8000`, used by next.config rewrites)

## Conventions

- **Frontend components:** PascalCase, `"use client"` directive, `@/` import alias, Tailwind utility classes inline
- **Backend modules:** snake_case, private functions prefixed with `_`, constants in UPPER_SNAKE_CASE
- **Global singletons:** Embedding model and FAISS indices are lazily loaded and cached in module-level variables (`_model`, `_indexes` dicts in `embedding.py`)
- **SSE format:** See "SSE Streaming Protocols" above — the two endpoints differ
- **Database:** SQLite with `get_db()` context manager, auto-migrations on startup
- **LLM output is plain text** (no Markdown) with strict section structure enforced by system prompt: 【核心洞察】, 【模式识别】, 【证据归因】
- **Per-user FAISS indices** stored as `{sha256(nickname)[:16]}.faiss` files in `data/faiss_index/`

## Deployment

- **Frontend → Vercel:** auto-deploys on push to main
- **Backend → Railway:** NIXPACKS builder, port 8000, health check at `GET /api/health`, Procfile runs uvicorn
