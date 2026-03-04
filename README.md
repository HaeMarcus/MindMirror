<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/mirror_1fa9e.png" width="80" />
</p>

<h1 align="center">MindMirror</h1>

<p align="center">
  <strong>基于多源数据的 AI 自我觉察助手</strong>
</p>

<p align="center">
  <a href="#-项目简介">项目简介</a> •
  <a href="#-功能亮点">功能亮点</a> •
  <a href="#%EF%B8%8F-技术架构">技术架构</a> •
  <a href="#-快速开始">快速开始</a>
</p>

---

## 📖 项目简介

我是 Marcus，一名试图通过数据打量生活的数字产品爱好者。长期以来，我的灵感散落在 Flomo，总结沉淀在 Obsidian，消费欲膨胀在记账软件里。这些跨平台的数字足迹构成了我最真实的“数字镜像”。

前段时间，我回看这些跨平台的数据，却发现它们彼此割裂。于是脑海中忽然闪出一个念头，**如果把这些数据整合起来交给 AI，它会怎么看我？：如果 AI 作为一个第三方观察者，通过这些多维数据重新解析我，它能打破我自我认知的“信息茧房”吗？**

现有的 Chatbot 大多健忘，而主流的 AI 助手又因为过于“讨好”而显得平庸。我渴望的是一种基于证据链的深度洞察：当你高喊“终身学习”时，若账单显示娱乐支出激增、复盘中焦虑词云密布，这种“知行不一”才是 AI 应该捕捉到的真实。

于是我决定自己动手，开启了一场 Vibe Coding 之旅：从写下第一行 PRD 开始，到前后端实现、RAG 配置调优、记忆模块设计、Prompt 工程... 直到部署上线。我给它起名 MindMirror，寓意“思维之镜”。

MindMirror 不负责讨好，只负责照见。 它试图通过多维数据的关联，帮用户发现连自己都可能忽略的行为模式和认知盲区。MindMirror 尚在雏形，但欢迎大家前来“照镜子”，听听 AI 对你的“人间清醒”式告白。

> 🌐 **直接试试：** [mind-mirror-liart.vercel.app](https://mind-mirror-liart.vercel.app/)&emsp;|&emsp;📄 **产品需求文档：** [PRD](https://icnmqhcc34ly.feishu.cn/wiki/ENsuwN0p3iKvf9k7AHqcoRi5nOb)


## ✨ 功能亮点

### 📂 多维数据融合

不是单一数据源的分析，而是把**你说的话、你写的字、你花的钱**交叉比对：

| 数据类型 | 格式 | 捕捉维度 |
|---------|------|---------|
| 日常记录 | Flomo `.html` 导出 | 碎片化想法、情绪状态 |
| 个人复盘 | Markdown `.md` | 自我认知、目标规划 |
| 财务账单 | 钱迹 `.csv` 导出 | 真实行为、消费偏好 |

拖拽上传，自动解析，实时进度条告诉你向量化到了第几条 📊

多维数据的交叉才是洞察的关键——你嘴上说想学习，账单说你在消费娱乐，复盘说你在焦虑，这三条线索交织在一起，比任何单一数据源都更接近真相。

### 🧠 三层记忆系统

AI 不只是回答问题，它在**记住你**：

| 层级 | 机制 | 作用 |
|------|------|------|
| 短期记忆 | 最近 15 轮对话 | 保持上下文连贯 |
| 中期记忆 | 滚动摘要（每 7 轮更新） | 跨对话的主题延续 |
| 长期记忆 | 用户画像 JSON | 深层认知模式积累 |

对话越多，AI 越懂你。第一次聊和第十次聊，感受完全不同。

### 💬 单窗口陪伴感

没有复杂的导航、没有多个页面切换。一个对话窗口，就像和一个了解你的朋友聊天：

- **结构化输出**：每次回答都有核心洞察、模式识别、证据归因三个板块
- **流式渲染**：彩色卡片逐步生长，不是一次性甩出一堵墙
- **准确度反馈**：每条回答下方的 👍👎 是产品的北极星指标
- **昵称即入口**：不需要注册登录，输入昵称就开始

## 🏗️ 技术架构

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
│  ┌──────────────────┐  ┌───────────────── ────┐ │
│  │ bge-small-zh-v1.5│  │ Claude Sonnet        │ │
│  │ Embedding (512d) │  │ Structured Output    │ │
│  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**核心选型理由：**
- **bge-small-zh-v1.5**：中文语义检索效果好，体积小速度快
- **FAISS IndexFlatIP**：L2 归一化后做内积 = cosine similarity，小规模精确搜索
- **SQLite**：单文件数据库，部署简单，够用就是最好的


## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+
- Anthropic API Key

### 后端

```bash
cd backend
python -m venv venv && source venv/bin/activate
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

打开 `http://localhost:3000`，输入昵称，上传数据，开始对话 🎉

> 💡 也可以选择云端部署——项目已适配 Vercel（前端）+ Railway（后端）方案，开箱即用。

## 📁 项目结构

```
MindMirror/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置
│   │   ├── database.py       # SQLite + 自动迁移
│   │   ├── embedding.py      # 向量化 + FAISS
│   │   ├── retriever.py      # 检索管线
│   │   ├── memory.py         # 三层记忆
│   │   ├── llm.py            # LLM 调用
│   │   ├── parsers/          # 三种格式解析器
│   │   └── routers/          # API 路由
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # React 组件
│   └── lib/api.ts            # API 客户端
└── 核心说明文档/              # PRD & 架构设计
```

## 📄 License

MIT

---

<p align="center">
  用数据理解自己，比你想象的更有趣。<br/>
  <sub>Built with Claude</sub>
</p>
