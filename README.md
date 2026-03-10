<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/mirror_1fa9e.png" width="80" />
</p>

<h1 align="center">MindMirror</h1>

<p align="center">
  <strong>基于多源数据的 AI 自我觉察助手</strong>
</p>

<p align="center">
  <a href="#-项目简介">项目简介</a> •
  <a href="#-产品设计">产品设计</a> •
  <a href="#-核心功能">核心功能</a> •
  <a href="#%EF%B8%8F-技术实现">技术实现</a> •
  <a href="#-快速开始">快速开始</a>
</p>

---

## 📖 项目简介

Hi，我是 Marcus，一名数字产品爱好者。长期以来，我利用各种软件记录生活的方方面面。我日常的灵感散落在 Flomo，复盘反思沉淀在 Obsidian，消费记录则留在记账软件里。这些跨平台的数字足迹构成了我最真实的"数字镜像"。

前段时间，我回看这些跨平台的数据，却发现它们彼此割裂。于是脑海中忽然闪出一个念头——**如果把这些数据整合起来交给 AI，它会怎么看我？当 AI 作为一个第三方观察者，通过这些多维数据重新解析我，它能打破我自我认知的"信息茧房"吗？**

现有的 Chatbot 大多健忘，而主流的 AI 助手又因为过于"讨好"而显得平庸。我渴望的是一种基于证据链的深度洞察：当你高喊"终身学习"时，若账单显示娱乐支出激增、复盘中焦虑词云密布，这种"知行不一"才是 AI 应该捕捉到的真实。

于是我决定自己动手，开启了一场 Vibe Coding 之旅：从写下第一行 PRD 开始，到前后端实现、RAG 配置调优、记忆模块设计、Prompt 工程... 直到部署上线。我给它起名 MindMirror，寓意"思维之镜"。

> 线上体验地址见右侧 About 栏，[产品需求文档](https://icnmqhcc34ly.feishu.cn/wiki/ENsuwN0p3iKvf9k7AHqcoRi5nOb)欢迎查阅，试用和交流。


## 🎯 需求痛点

在调研和自身体验中，我发现了三个核心矛盾：

| 痛点 | 现有方案的不足 | MindMirror 的切入 |
|------|--------------|------------------|
| **数据孤岛** — 日记、复盘、账单散落在不同平台 | 各工具只分析自身数据，无法交叉验证 | 三源数据融合，让"说的 × 写的 × 花的"互相对照 |
| **AI 讨好症** — 主流 AI 助手倾向正面反馈 | 用户得到的是安慰而非洞察 | "冷镜"人格设计：证据驱动，不回避矛盾，直指盲区 |
| **对话健忘** — Chatbot 缺乏持续记忆 | 每次对话都从零开始，无法积累认知 | 三层记忆系统：越聊越懂你，第一次和第十次体验截然不同 |


## ✨ 产品设计

### 📂 多维数据融合

把**你说的话、你写的字、你花的钱**交叉比对：

| 数据类型 | 格式 | 捕捉维度 |
|---------|------|---------|
| 日常记录 | Flomo `.html` | 碎片化想法、情绪状态 |
| 个人复盘 | Markdown `.md` | 自我认知、目标规划 |
| 财务账单 | 账单 `.csv` | 真实行为、消费偏好 |

你嘴上说想学习，账单说你在消费娱乐，复盘说你在焦虑——这三条线索交织在一起，比任何单一数据源都更接近真相。

### 🗂️ 三层记忆系统

| 层级 | 触发机制 | 作用 |
|------|---------|------|
| 短期记忆（Working Memory） | 最近 3 轮对话 | 保持当前语义连贯 |
| 中期记忆（Episodic Memory） | 首轮生成，每 5 轮更新 | 滚动摘要，跨对话主题延续 |
| 长期记忆（Semantic Memory） | 首轮生成，每 10 轮更新 | 用户画像 JSON + 大五人格 |

三个层级形成 3 < 5 < 10 的递增更新频率，短期快速响应、中期捕捉趋势、长期沉淀人格。首轮即触发中长期记忆的 bootstrap，确保用户第一次对话就能获得画像级洞察。

### 💬 单窗口陪伴感

没有复杂的导航，一个对话窗口，像和一个了解你的朋友聊天：

- **结构化输出**：核心洞察 → 模式识别 → 证据归因，每次回答都有据可查
- **流式渲染**：彩色卡片逐字生长，实时感受 AI 思考的过程
- **大五人格雷达图**：随对话深入，侧边栏动态生成你的人格画像
- **准确度反馈**：每条回答下方的 👍👎 驱动产品迭代


## 🏗️ 技术实现

```
┌─────────────────────────────────────────────────┐
│                  Frontend                       │
│         Next.js 15 + React 19 + Tailwind        │
│       SSE Streaming · localStorage 持久化        │
└────────────────────┬────────────────────────────┘
                     │ REST + SSE
┌────────────────────▼────────────────────────────┐
│                  Backend                        │
│              FastAPI + SQLite                   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Parsers  │  │ Memory   │  │  Retriever    │  │
│  │ HTML/MD/ │  │ 3-Layer  │  │ FAISS + Rerank│  │
│  │ CSV      │  │ System   │  │ + Compress    │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ bge-small-zh-v1.5│  │ Claude Sonnet        │ │
│  │ Embedding (512d) │  │ Structured Output    │ │
│  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 选型决策与权衡

| 选型 | 选择 | 取舍考量 |
|------|------|---------|
| **Embedding** | bge-small-zh-v1.5（本地） | 中文语义效果优秀、512 维够用、无需外部 API 调用，用户数据不出本机 |
| **向量库** | FAISS IndexFlatIP | 小规模精确搜索足够，L2 归一化后内积 = cosine similarity，无需 Pinecone 等外部服务 |
| **数据库** | SQLite | 单文件部署、零运维，对当前用户规模而言性能远超需求 |
| **检索策略** | 关键词规则 Rerank | 无需额外 Rerank 模型，通过源类型关键词匹配（财务词 → CSV boost 1.3x）实现 source-aware 检索 |
| **流式输出** | SSE（非 WebSocket） | 单向推送场景下 SSE 更轻量，原生支持自动重连，部署兼容性好 |

### 数据流：从上传到洞察

```
用户上传文件 → Parser 解析为 Chunks → bge-small-zh 向量化 → FAISS 索引 + SQLite 存储
                                                                        ↓
用户提问 → Query Embedding → FAISS Top-12 → Source-Aware Rerank → Evidence Compression
                                                                        ↓
短期记忆 + 滚动摘要 + 用户画像 + 压缩证据 → Claude Sonnet → 结构化流式输出
                                                                        ↓
                                              每 5 轮更新摘要 · 每 10 轮更新画像
```


## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+
- Anthropic API Key

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
```

打开 `http://localhost:3000`，输入昵称，上传数据，开始对话。

> 项目已适配 Vercel（前端）+ Railway（后端）的云端部署方案。


## 📁 项目结构

```
MindMirror/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置常量
│   │   ├── database.py       # SQLite + 自动迁移
│   │   ├── embedding.py      # 向量化 + FAISS 索引
│   │   ├── retriever.py      # RAG 检索管线
│   │   ├── memory.py         # 三层记忆系统
│   │   ├── llm.py            # Claude API + Prompt 工程
│   │   ├── parsers/          # Flomo / MD / CSV 解析器
│   │   └── routers/          # API 路由（ingest + chat）
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # React 组件
│   └── lib/api.ts            # API 客户端 + SSE 处理
└── CLAUDE.md                 # AI 辅助开发指引
```

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。如果这个项目对你有帮助，欢迎 Star 支持。

---

<p align="center">
  用数据理解自己，比你想象的更有趣。<br/>
  <sub>Built with Claude</sub>
</p>
