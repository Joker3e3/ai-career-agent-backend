# AI Career Analysis Agent

AI Career Analysis Agent 是一个基于 Agentic RAG 的求职分析系统，面向 AI 全栈 / AI Agent 岗位求职场景。系统通过 RAG 检索候选人简历与项目经历证据，再由 LangGraph Agent Workflow 对岗位 JD 进行结构化分析、能力匹配、差距识别，并生成个性化学习路线、面试准备建议和投递邮件草稿。

项目不仅实现了传统 RAG 问答，还进一步将 RAG 作为 Agent 的工具能力接入工作流，实现了 Query Decomposition、Evidence-first、Reflection / Retry、Redis 短期 Memory、Human-in-the-loop 确认流程等 Agent 工程能力。

### AI Career Analysis Agent（Agentic RAG 求职分析系统）

基于 LangGraph 与 Agentic RAG 构建 AI 求职分析系统，实现岗位 JD 分析、简历 Evidence Retrieval、能力匹配分析、学习路线生成与 Human-in-the-loop Workflow。

- 基于 LangGraph 构建多节点 Agent Workflow，实现 JD Analysis、Query Decomposition、Evidence Retrieval、Reflection / Retry、Report Generation 等 Agent 流程
- 将 RAG Retriever 作为 Agent Tool 接入 Workflow，基于 Hybrid Retrieval（Vector + BM25）、Rerank 与 Context Compression 提升 Evidence 召回质量
- 实现 Evidence-first Generation，所有能力分析与岗位匹配均基于 RAG 检索 evidence，降低 LLM 幻觉问题
- 实现 Query Decomposition，将岗位需求拆分为前端、后端、AI、Infra 等多个技能维度进行独立 Retrieval
- 实现 bounded Reflection / Retry Workflow，当 evidence 不足时自动生成 Retry Query 并重新检索，避免无限 Agent Loop
- 基于 Redis 实现 Workflow Runtime State、Human Confirmation State 与短期 Memory，支持 Pause / Resume Workflow
- 实现 Human-in-the-loop Workflow：生成投递草稿后进入 pending_confirmation 状态，用户确认后恢复 Workflow 执行
- 前端基于 Vue3 实现 Agent 交互页面与 Markdown 报告展示

## Core Features

### 1. Agentic RAG Resume Retrieval

系统将候选人简历构建为向量知识库，并通过 Hybrid Retrieval（Vector + BM25）进行检索，再结合 Rerank 与 Context Compression 提升召回质量。

与传统 RAG 不同，RAG 在本项目中不仅用于问答，而是作为 Agent Workflow 的工具能力，用于支持岗位匹配分析。

---

### 2. Evidence-first Resume Analysis

系统不会直接让 LLM“猜测”候选人能力，而是要求所有分析必须基于 RAG 检索到的简历 evidence。

Agent 会优先检索候选人的真实项目、技能与教育经历，再生成能力画像与岗位匹配分析，以减少幻觉问题。

---

### 3. Query Decomposition

系统会先对岗位 JD 进行结构化拆解，将岗位需求分解为多个技能维度（前端、后端、AI、Infra 等），再针对每个维度生成独立 retrieval query。

相比单次检索，Query Decomposition 能提升复杂岗位的召回覆盖率。

---

### 4. Reflection / Retry Workflow

当 evidence 不足时，Agent 会进行 Reflection，判断当前检索结果是否可靠，并自动生成 retry query 重新检索。

系统采用 bounded retry 机制，避免无限 Agent Loop 导致的 Token 与延迟失控。

---

### 5. Human-in-the-loop Workflow

系统实现了两阶段 Human-in-the-loop Workflow：

1. Agent 生成分析报告与投递草稿
2. Workflow 进入 pending_confirmation 状态
3. 用户确认后恢复 Workflow

系统通过 Redis 保存 workflow runtime state 与 confirmation state，实现 pause / resume workflow。

---

### 6. Redis-based Runtime State

系统基于 Redis 实现：

- 短期 Conversation Memory
- Workflow Runtime State
- Human Confirmation State
- Retry Runtime Metadata

支持 Agent Workflow 的状态恢复与运行追踪。

## Architecture

Vue Frontend
↓
FastAPI Backend
↓
LangGraph Agent Workflow
├── JD Analysis
├── Query Decomposition
├── RAG Evidence Retrieval
├── Reflection / Retry
├── Resume Profile Extraction
├── Match Analysis
├── Learning Plan Generation
├── Interview Tips Generation
├── Cover Letter Generation
├── Human-in-the-loop Confirmation
└── Workflow Runtime Persistence
↓
Redis Runtime Store
↓
Chroma Vector Database
↓
Resume Knowledge Base

Tech Stack
Frontend
Vue 3
Vue Router
Markdown Rendering
Backend
FastAPI
LangChain
LangGraph
Redis
ChromaDB
AI / RAG
Hybrid Retrieval (Vector + BM25)
Rerank
Context Compression
Query Decomposition
Reflection / Retry
Evidence-first Generation
Workflow Runtime
Redis-based Runtime State
Human-in-the-loop Workflow
Pause / Resume Workflow
Confirmation Runtime State

## Agent Workflow

系统基于 LangGraph 构建 Agent Workflow，而不是简单的单次 LLM 调用。

整体流程如下：

User Input JD
↓
JD Analysis
↓
Query Decomposition
↓
RAG Evidence Retrieval
↓
Reflection / Retry
↓
Resume Profile Extraction
↓
Match Analysis
↓
Learning Plan Generation
↓
Interview Tips Generation
↓
Cover Letter Generation
↓
Generate Report
↓
Human-in-the-loop Confirmation
↓
Pause Workflow
↓
User Confirm
↓
Resume Workflow
Reflection / Retry

系统会自动判断当前 evidence 是否足够。

当 evidence 不足时：

Agent 自动进行 Reflection
生成 Retry Query
再次调用 RAG Retriever
合并新 evidence
限制最大 Retry 次数，避免无限 Agent Loop
Human-in-the-loop

系统实现了基于 Redis Runtime State 的 Human-in-the-loop Workflow。

Workflow 在生成投递草稿后进入：

waiting_human_confirmation

状态。

用户确认后：

前端调用 confirm API
系统恢复 workflow state
confirm_graph 继续执行
workflow completed
