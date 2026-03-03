<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/mirror_1fa9e.png" width="80" />
</p>

<h1 align="center">MindMirror</h1>

<p align="center">
  <strong>基于多源数据的 AI 自我觉察助手 🪞</strong>
</p>

<p align="center">
  <a href="#项目简介">项目简介</a> •
  <a href="#功能亮点">功能亮点</a> •
  <a href="#技术架构">技术架构</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#部署指南">部署指南</a>
</p>

---

## 📖 项目简介

我一直对 AI 产品很感兴趣，想尝试自己从 0 到 1 构建一个完整的 AI 应用。某天写完月度复盘，翻了翻之前的日记和账单，突然冒出一个念头：**如果把这些散落各处的个人数据喂给 AI，它会怎么看我？**

试了几个市面上的 AI 性格测试，发现它们都在给你贴标签——"你是 INTJ"就完事了。但我想要的不是标签，而是**基于我自己真实数据的、有证据归因的深度洞察**。比如：你嘴上说想学习，账单却显示娱乐支出在涨，复盘里又反复提到焦虑——这三条线索交织在一起，才是真正有价值的自我觉察。

于是就有了 MindMirror。它把日记、复盘、账单这些多维数据汇聚起来，通过语义检索 + 大模型，帮你发现那些自己可能忽略的行为模式、情绪倾向和认知盲区。像一面镜子，用你自己的数据照见你自己。

📄 **产品文档：** [PRD 产品需求文档](https://icnmqhcc34ly.feishu.cn/wiki/ENsuwN0p3iKvf9k7AHqcoRi5nOb)

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

- **结构化输出**：每次回答都有核心洞察、证据归因、防御机制提醒、下一步建议
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


## 🤔 设计思考

几个我认为有意思的设计决策：

1. **为什么是结构化输出而不是自由聊天？** —— 洞察不是越长越好。固定结构逼 AI 给出证据和行动建议，而不是空泛地聊天。

2. **为什么加"防御机制"板块？** —— 来自心理学的启发。当 AI 指出你的盲区时，你的第一反应通常是否认。提前点破这一层，反而让洞察更容易被接受。

3. **为什么用昵称而不是账号密码？** —— MVP 阶段追求最低使用门槛。一个昵称就够了，不需要记密码、不需要邮箱验证。

4. **为什么反馈按钮是"北极星指标"？** —— 对于洞察类产品，准确度就是一切。用户觉得不准，再花哨的功能也没意义。


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

## ☁️ 部署指南

项目已配置好 **Vercel（前端）+ Railway（后端）** 的部署方案：

| 服务 | 平台 | 关键配置 |
|------|------|---------|
| Frontend | Vercel | `BACKEND_URL` 环境变量指向后端 |
| Backend | Railway | Root Directory 设为 `backend`，配置 `ANTHROPIC_API_KEY` |

> 💡 Railway 使用 CPU-only PyTorch 以控制镜像体积在 4GB 以内。可选挂载 Volume 并设置 `DATA_DIR` 环境变量实现数据持久化。

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
