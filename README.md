<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/mirror_1fa9e.png" width="80" />
</p>

<h1 align="center">MindMirror</h1>

<p align="center">
  <strong>一面用数据照见自己的镜子 🪞</strong><br/>
  基于多源个人数据的 RAG + AI 自我觉察助手
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#功能亮点">功能亮点</a> •
  <a href="#技术架构">技术架构</a> •
  <a href="#部署指南">部署指南</a> •
  <a href="#产品文档">产品文档</a>
</p>

---

## 💡 这是什么？

你有没有想过，如果把你的**日记、复盘笔记、消费账单**喂给 AI，它会怎么看你？

MindMirror 就是这样一个实验——把散落在各处的个人数据汇聚起来，用 RAG 检索 + Claude 大模型，帮你从数据中发现那些自己可能忽略的行为模式、情绪倾向和认知盲区。

不是那种"你是 INTJ"就完事的性格测试，而是**基于你真实数据的、有证据归因的深度洞察**。

> 🧠 "你最近三个月在'学习'类支出占比下降了 40%，但你的复盘里反复提到想要成长——这种言行不一致可能是一个值得觉察的信号。"

## ✨ 功能亮点

### 📂 多源数据接入
| 数据类型 | 格式 | 示例 |
|---------|------|------|
| 日常记录 | Flomo `.html` 导出 | 碎片化想法、情绪记录 |
| 个人复盘 | Markdown `.md` | 月度复盘、年度总结 |
| 财务账单 | 钱迹 `.csv` 导出 | 消费记录、收支分析 |

拖拽上传，自动解析，实时进度条告诉你向量化到了第几条 📊

### 🔍 智能检索 + 证据归因
不是简单的关键词搜索。每条洞察都会告诉你"我是根据你哪份数据、哪个时间段得出的结论"：
- **Source-Aware Reranking**：问消费习惯优先匹配账单，问情绪状态优先匹配日记
- **Evidence Compression**：去重 + 截断，把最相关的证据喂给模型

### 🧩 四段结构化输出
每次回答都按固定结构呈现，拒绝模糊的鸡汤：

| 板块 | 作用 |
|------|------|
| 🔴 **核心洞察** | 直击要害的发现 |
| 🔵 **证据归因** | 数据来源和推理链 |
| 🟡 **防御机制** | 你可能的心理防御反应 |
| 🟢 **实验性下一步** | 可落地的行动建议 |

### 🧠 三层记忆系统
| 层级 | 机制 | 更新频率 |
|------|------|---------|
| 短期记忆 | 最近 15 轮对话 | 实时 |
| 中期记忆 | Claude 生成的滚动摘要 | 每 7 轮 |
| 长期记忆 | 用户画像 JSON | 低频 |

对话越多，AI 越懂你。

### 👥 多用户隔离
没有复杂的登录系统——输入昵称就能开始。不同用户的数据、对话、记忆完全隔离。

### 👍👎 准确度反馈
每条回答下方的反馈按钮是我的"北极星指标"。用户觉得准不准，比任何技术指标都重要。

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│                  Frontend                        │
│         Next.js 15 + React 19 + Tailwind         │
│     SSE Streaming · localStorage 用户持久化       │
└────────────────────┬────────────────────────────┘
                     │ REST + SSE
┌────────────────────▼────────────────────────────┐
│                  Backend                         │
│              FastAPI + SQLite                     │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Parsers  │  │ Memory   │  │  Retriever    │  │
│  │ HTML/MD/ │  │ 3-Layer  │  │ FAISS + Rerank│  │
│  │ CSV      │  │ System   │  │ + Compress    │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ bge-small-zh-v1.5│  │ Claude claude-sonnet-4-6        │  │
│  │ Embedding (512d) │  │ Structured Output    │  │
│  └──────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────┘
```

**核心选型理由：**
- **Claude claude-sonnet-4-6**：中文洞察能力强，结构化输出稳定
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
│   │   ├── retriever.py      # RAG 检索管线
│   │   ├── memory.py         # 三层记忆
│   │   ├── llm.py            # Claude 调用
│   │   ├── parsers/          # 三种格式解析器
│   │   └── routers/          # API 路由
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # React 组件
│   └── lib/api.ts            # API 客户端
└── 核心说明文档/              # PRD & 架构设计
```

## 🤔 设计思考

做这个项目的初衷很简单：**市面上的 AI 性格测试都在给你贴标签，但很少有人用你自己的数据来照见你自己。**

几个我认为有意思的设计决策：

1. **为什么是四段结构而不是自由输出？** —— 洞察不是越长越好。固定结构逼 AI 给出证据和行动建议，而不是空泛地聊天。

2. **为什么加"防御机制"板块？** —— 来自心理学的启发。当 AI 指出你的盲区时，你的第一反应通常是否认。提前点破这一层，反而让洞察更容易被接受。

3. **为什么用昵称而不是账号密码？** —— MVP 阶段追求最低使用门槛。一个昵称就够了，不需要记密码、不需要邮箱验证。

4. **为什么反馈按钮是"北极星指标"？** —— 对于洞察类产品，准确度就是一切。用户觉得不准，再花哨的功能也没意义。

## 📝 产品文档

- [PRD 产品需求文档](<!-- 在此填入链接 -->)
- [技术架构设计](<!-- 在此填入链接 -->)

## 📄 License

MIT

---

<p align="center">
  用数据理解自己，比你想象的更有趣。<br/>
  <sub>Built with ❤️ and Claude</sub>
</p>
