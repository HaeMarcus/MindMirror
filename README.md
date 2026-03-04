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

我一直是一个喜欢思考、复盘、记录的人。Flomo 里攒了上千条碎片想法，Obsidian 存着每年的年度总结和月度复盘，记账软件忠实记录了每一笔开销——这些散落在不同工具里的数字足迹，拼在一起，其实就是一个完整的"我"。

某天写完月度复盘，顺手翻了翻过去半年的日记和账单，突然冒出一个念头——**如果把这些数据整合起来交给 AI，它会怎么看我？**

试了一圈市面上的产品，发现要么过于讨好、给你贴个 MBTI 标签就完事了，要么只能处理单轮对话、无法长期积累认知，要么根本不支持多源文件导入。但我想要的不是标签，而是**基于真实数据的、有证据归因的深度洞察**。你嘴上说想学习，账单却显示娱乐支出在涨，复盘里又反复提到焦虑——多条线索交织在一起，才是真正有价值的自我觉察。

于是我决定自己动手。从写下第一行 PRD 开始，到前后端实现、向量检索调优、Prompt 工程，一路 **Vibe Coding** 到部署上线。整个过程最让我着迷的是**产品直觉和工程实现之间的反复校准**——你在文档里写下的每一个设计假设，最终都要在真实的用户对话中被验证或推翻。

MindMirror 就这样诞生了。它像一面镜子，用你自己的多维数据，照见那些连你自己都可能忽略的行为模式和认知盲区。

> 🌐 **直接试试：** [mind-mirror-liart.vercel.app](https://mind-mirror-liart.vercel.app/)&emsp;|&emsp;📄 **产品设计全文：** [PRD 产品需求文档](https://icnmqhcc34ly.feishu.cn/wiki/ENsuwN0p3iKvf9k7AHqcoRi5nOb)


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
