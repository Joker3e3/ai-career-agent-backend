# AI Career Agent Backend

面向求职分析场景的 AI Agent 后端个人项目，用于验证 Agent Workflow、RAG 工具调用、异步任务、长期记忆、人工确认和可观测性等工程化链路。

## 1. Project Overview / 项目简介

AI Career Agent Backend 是一个 Personal Project / 个人独立项目。它接收用户的岗位 JD、用户标识、会话标识和补充简历文本，调用外部简历 RAG 服务检索候选人证据，并生成岗位匹配分析、学习或面试建议、Cover Letter 草稿和可查询的 Agent 执行 trace。

这个项目的目标不是构建生产级高可用招聘平台，而是把 AI Agent / RAG 应用中常见的工程问题串成一个可运行后端：任务提交、JD 分析、检索规划、工具调用、ReAct 反思、报告生成、人工确认、状态查询和运行记录落库。

当前部署定位为 Local / Docker Compose deployment for personal project demonstration。它适合用于技术面试、工程学习和本地演示，不包含线上用户体系、大规模并发能力或完整评测平台。

## 2. Repository Role / 当前仓库定位

当前仓库是 `ai-career-agent-backend`，在整体系统中承担求职分析 Agent 后端角色。

相关仓库关系：

- Frontend: `https://github.com/Joker3e3/ai-agent-rag-frontend`
- RAG Backend: `https://github.com/Joker3e3/ai-rag-knowledge-base-backend`
- Agent Backend: `https://github.com/Joker3e3/ai-career-agent-backend`

服务关系：

- `ai-agent-rag-frontend` 调用本仓库提供的 Career Agent API，提交 JD 分析任务、轮询状态、展示报告和 trace。
- 本仓库依赖 `ai-rag-knowledge-base-backend` 提供的 Resume RAG 能力，当前通过 `RAG_SERVICE_URL/retrieve_evidence` 获取简历证据。
- PostgreSQL 保存 agent runs、agent steps、tool calls、human confirmations 和 user memories。
- Redis 同时用于 Celery broker/result backend，以及 workflow state / confirmation state 的短期状态存储。

## 3. Architecture / 系统架构

```mermaid
flowchart LR
    User["User"] --> Frontend["Vue Frontend<br/>ai-agent-rag-frontend"]
    Frontend --> AgentAPI["FastAPI Agent Backend<br/>ai-career-agent-backend"]

    AgentAPI --> Submit["Submit Workflow<br/>POST /career_agent/analyze"]
    AgentAPI --> Query["Status / Report / Trace APIs"]
    AgentAPI --> Confirm["Human Confirmation<br/>POST /career_agent/confirm"]
    AgentAPI --> Cancel["Cancel Workflow<br/>POST /career_agent/cancel/{workflow_id}"]

    Submit --> Celery["Redis + Celery Queue"]
    Celery --> Workflow["LangGraph Workflow"]
    RecoveryScript["Recovery Script<br/>scripts.requeue_stuck_workflows"] --> Celery
    RecoveryScript --> Resume["Checkpoint Resume"]

    Workflow --> LoadMemory["Load Memory"]
    Workflow --> JD["JD Analysis"]
    JD --> Planner["Strategy Planner"]
    Planner --> QueryPlan["Retrieval Query Builder"]
    QueryPlan --> RAGTool["Resume RAG Tool"]
    RAGTool --> RAGBackend["RAG Backend Service<br/>ai-rag-knowledge-base-backend"]
    RAGBackend --> RAGTool
    RAGTool --> Reflection["Reflection Loop"]
    Reflection -->|need more evidence| RAGTool
    Reflection --> Profile["Resume Profile Extraction"]
    Profile --> Match["Job Match"]
    Match --> Report["Report Generation"]
    Report --> MemoryWrite["Memory Write"]
    MemoryWrite --> Human["Human Confirmation"]

    Workflow --> CheckpointManager["Checkpoint Manager"]
    CheckpointManager --> RedisState[(Redis Workflow State)]
    CheckpointManager --> WorkflowCheckpoint[(PostgreSQL<br/>workflow_checkpoints)]
    Resume --> CheckpointManager

    Workflow --> TraceCollector["Trace Collector"]
    TraceCollector --> AgentSteps[(agent_steps)]
    TraceCollector --> ToolCalls[(tool_calls)]

    Workflow --> CancellationChecker["Cancellation Checker"]
    CancellationChecker --> AgentRuns[(agent_runs status)]
    Cancel --> AgentRuns

    Workflow --> Postgres[(PostgreSQL)]
    Query --> Postgres
    Query --> AgentSteps
    Query --> ToolCalls
    Human --> Postgres
    Confirm --> Postgres
    Human --> RedisState
    Confirm --> RedisState
```

核心工作流基于 `agents/career_graph.py` 中的 LangGraph `StateGraph`：

```mermaid
flowchart TD
    START(["START"]) --> route_resume["route_resume"]
    route_resume -->|no checkpoint| load_memory["load_memory"]
    route_resume -->|resume_from_node| retrieve_resume_evidence
    route_resume -->|resume_from_node| reflect_evidence
    route_resume -->|resume_from_node| match_job
    route_resume -->|resume_from_node| generate_report
    load_memory --> analyze_jd["analyze_jd"]
    analyze_jd --> plan_career_analysis["plan_career_analysis"]
    plan_career_analysis --> build_retrieval_queries["build_retrieval_queries"]
    build_retrieval_queries --> cp_query["CP: Recovery"]
    cp_query --> retrieve_resume_evidence["retrieve_resume_evidence"]
    retrieve_resume_evidence --> cp_evidence["CP: Recovery"]
    cp_evidence --> reflect_evidence["reflect_evidence"]
    reflect_evidence -->|act and retry available| execute_react_action["execute_react_action"]
    execute_react_action --> reflect_evidence
    reflect_evidence -->|continue or max retry reached| extract_resume_profile["extract_resume_profile"]
    extract_resume_profile --> cp_profile["CP: Recovery"]
    cp_profile --> match_job["match_job"]
    match_job -->|match_score >= 80| generate_interview_tips["generate_interview_tips"]
    match_job -->|match_score < 80| generate_learning_plan["generate_learning_plan"]
    generate_interview_tips --> generate_cover_letter["generate_cover_letter"]
    generate_learning_plan --> generate_cover_letter
    generate_cover_letter --> cp_cover["CP: Recovery"]
    cp_cover --> generate_report["generate_report"]
    generate_report --> save_memory["save_memory"]
    save_memory --> create_confirmation["create_confirmation"]
    create_confirmation --> cp_confirmation["CP: Confirmation"]
    cp_confirmation --> END([END])
```

## 多仓库启动顺序

当前系统由以下三个仓库共同组成：

1. 启动 RAG 知识库后端：`ai-rag-knowledge-base-backend`
   - 默认地址：`http://localhost:8000`

2. 启动 Agent 后端：`ai-career-agent-backend`
   - 默认地址：`http://localhost:8001`

3. 启动前端项目：`ai-agent-rag-frontend`
   - 默认地址：`http://localhost:5173`

### 服务依赖关系

- Agent 后端通过 `RAG_SERVICE_URL` 调用 RAG 知识库服务，实现简历检索与证据获取能力。
- 前端项目同时调用 Agent 后端与 RAG 后端接口：
  - `VITE_AGENT_API_BASE_URL`
  - `VITE_RAG_API_BASE_URL`

### 整体调用链路

```text
Vue Frontend
    ↓
Agent Backend
    ↓
RAG Backend
    ↓
ChromaDB / Embedding / Retrieval
```

## 4. Core Features / 核心功能

- **JD 能力域分析**：通过 LLM 将岗位 JD 解析为岗位名称、岗位类型、能力要求、职责和背景要求，对应 `schemas/jd_schema.py` 和 `analyze_jd` 节点。
- **Strategy Planner**：根据 JD 分析结果生成检索维度、背景检索维度、重试策略和输出要求，对应 `plan_career_analysis`。
- **Resume RAG Tool**：通过 Tool Registry 调用 `resume_rag_retriever`，默认以 HTTP 方式请求外部 RAG 后端的 `/retrieve_evidence`。
- **ReAct-style Reflection Loop**：基于当前 evidence、query plan 和 available tools 判断是否需要补充检索，默认 `max_retry=1`，避免无限循环。
- **求职报告生成**：生成匹配分数、已匹配技能、缺失技能、优势风险、学习计划或面试建议，以及 Cover Letter 草稿。
- **Human Confirmation**：报告和投递草稿生成后进入 `waiting_human_confirmation`，用户可执行 `approve`、`revise` 或 `reject`，当前不会真实投递。
- **异步任务执行**：FastAPI 提交任务后立即返回 `workflow_id`，实际 Agent Workflow 由 Celery worker 执行。
- **Checkpoint Resume / Recovery**：Workflow 在关键节点保存 Checkpoint，Worker 异常退出后可通过恢复脚本重新投递，并从最近 Checkpoint 的后继节点继续执行。
- **Workflow Cancellation**：支持 `queued` 任务直接取消，以及 `running` 任务进入 `cancelling` 后在节点边界主动终止。
- **Trace / Observability**：节点执行记录写入 `agent_steps`，工具调用写入 `tool_calls`，包含节点状态、开始时间、结束时间、耗时、LLM token usage 和 model 信息，可通过 trace API 查询完整执行过程。

## 5. Tech Stack / 技术栈

**Backend**

- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn

**AI / Agent**

- LangGraph
- LangChain OpenAI-compatible `ChatOpenAI`
- DeepSeek-compatible Chat Completions API
- JSON mode structured output
- Tool Registry / Tool Calling
- Basic optional MCP stdio adapter

**Database / State**

- PostgreSQL
- Redis
- SQLAlchemy ORM

**Infra / Tooling**

- Docker
- Docker Compose
- Celery
- uv
- python-dotenv
- requests

**Frontend Integration**

- 本仓库不包含前端代码。
- 配套前端仓库为 `ai-agent-rag-frontend`，本地默认访问地址通常为 `http://localhost:5173`。

## 6. Project Structure / 目录结构

```text
.
├── main.py                         # FastAPI 入口，注册 CORS、工具和 API 路由
├── celery_app.py                   # Celery broker/result backend 配置
├── mcp_server.py                   # 可选 MCP Server，当前封装 resume_rag_retriever
├── Dockerfile                      # API/Worker 共用镜像
├── docker-compose.yml              # 本地 API、worker、PostgreSQL、Redis 编排
├── agents/
│   ├── career_graph.py             # LangGraph 主流程和确认流程
│   └── career/
│       ├── trace.py                # 节点和工具 trace 装饰器
│       ├── trace_summary.py        # trace 输入/输出摘要
│       └── state_policy.py         # Redis checkpoint 字段策略
├── tools/
│   ├── tool_registry.py            # ToolDefinition 与 ToolRegistry
│   ├── tool_executor.py            # 按工具名执行工具
│   ├── career_tools.py             # 注册求职分析工具
│   ├── rag_evidence_tool.py        # HTTP RAG 工具
│   └── mcp_tools.py                # MCP stdio 工具适配
├── services/
│   ├── career_analysis_service.py  # 提交任务并执行 Agent workflow
│   ├── agent_run_query_service.py  # workflow 状态和报告查询
│   ├── agent_trace_service.py      # trace 查询
│   ├── long_term_memory_service.py # 长期记忆读写
│   ├── workflow_state_service.py   # Redis workflow state
│   ├── checkpoint_runtime.py       # Workflow checkpoint 保存入口
│   ├── workflow_checkpoint_service.py # Redis / PostgreSQL checkpoint 读写
│   └── confirmation_service.py     # Redis confirmation state
├── database/
│   ├── models/                     # agent_runs、agent_steps、tool_calls 等模型
│   ├── repositories/               # 数据访问层
│   ├── database.py                 # SQLAlchemy engine/session
│   └── init_db.py                  # create_all 初始化入口
├── scrpits/                        # 脚本文件，重投脚本
├── routers/                        # 查询类 API 路由
├── schemas/                        # Pydantic schema
├── prompts/                        # LLM prompts
├── tasks/                          # Celery task
├── config/                         # 环境变量和日志配置
└── llms/                           # LLM client
```

## 7. Quick Start / 快速启动

### 7.1 Docker Compose 启动

启动本仓库前，先启动外部 RAG 后端 `ai-rag-knowledge-base-backend`，并确认它能提供 `POST /retrieve_evidence`。

```bash
git clone https://github.com/Joker3e3/ai-career-agent-backend.git
cd ai-career-agent-backend
```

从示例文件创建本地环境变量文件：

```bash
cp .env.example .env
```

Windows PowerShell 可使用：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，至少设置：

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

RAG_SERVICE_URL=http://host.docker.internal:8000
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_career_agent

REDIS_HOST=redis
REDIS_PORT=6379

USE_MCP_TOOLS=false
LOG_LEVEL=INFO
```

构建并启动服务：

```bash
docker compose up -d --build
```

首次启动后初始化数据库表：

```bash
docker compose exec api uv run python -m database.init_db
```

执行数据库迁移：

```bash
docker compose exec api uv run python -m database.migrations.run_migrations
```

访问 API 文档：

```text
http://localhost:8001/docs
```

如果配套前端已启动，可访问：

```text
http://localhost:5173
```

Docker Compose 会启动：

- `api`: FastAPI 服务，宿主机端口 `8001`
- `worker`: Celery worker
- `postgres`: PostgreSQL 16
- `redis`: Redis 7

### 7.2 本地 Python 启动

本地启动适合开发调试。需要自行准备 PostgreSQL、Redis 和外部 RAG 后端。

```bash
uv sync
```

设置本地 `.env` 示例：

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

RAG_SERVICE_URL=http://127.0.0.1:8000
DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/ai_career_agent

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

USE_MCP_TOOLS=false
LOG_LEVEL=INFO
```

初始化数据库：

```bash
uv run python -m database.init_db
```

执行数据库迁移：

```bash
uv run python -m database.migrations.run_migrations
```

启动 API：

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8010
```

启动 Celery worker：

```bash
uv run python -m celery -A celery_app worker --loglevel=INFO --pool=solo
```

本地 API 文档：

```text
http://127.0.0.1:8010/docs
```

## 8. Environment Variables / 环境变量

| 变量名               | 用途                                                                        |
| -------------------- | --------------------------------------------------------------------------- |
| `DEEPSEEK_API_KEY`   | DeepSeek 或兼容 OpenAI Chat Completions 服务的 API key。                    |
| `DEEPSEEK_BASE_URL`  | 兼容 OpenAI API 的模型服务 Base URL。                                       |
| `DEEPSEEK_MODEL`     | Agent 使用的 chat model 名称，默认可设置为 `deepseek-chat`。                |
| `RAG_SERVICE_URL`    | 外部 RAG 后端地址，本仓库会请求 `${RAG_SERVICE_URL}/retrieve_evidence`。    |
| `DATABASE_URL`       | PostgreSQL 连接字符串，供 FastAPI 和 Celery worker 使用。                   |
| `REDIS_HOST`         | Redis 主机名，Docker Compose 中使用 `redis`，本地开发通常使用 `127.0.0.1`。 |
| `REDIS_PORT`         | Redis 端口，默认 `6379`。                                                   |
| `REDIS_DB`           | Redis DB 编号，代码默认 `0`。                                               |
| `REDIS_ENABLED`      | 是否启用 Redis 相关状态能力，代码默认启用。                                 |
| `SESSION_MEMORY_TTL` | session memory 过期时间，单位秒。                                           |
| `WORKFLOW_STATE_TTL` | workflow state 过期时间，单位秒。                                           |
| `CONFIRMATION_TTL`   | confirmation state 过期时间，单位秒。                                       |
| `USE_MCP_TOOLS`      | 是否通过 MCP stdio 适配层调用 RAG 工具，默认 `false`。                      |
| `LOG_LEVEL`          | 应用日志级别，例如 `INFO`、`DEBUG`。                                        |

不要把真实 API key 写入 README 或提交到 Git 仓库。`.env` 应仅用于本地运行。


## 9. 故障恢复（Recovery）

### 9.1 Workflow Checkpoint

在关键节点保存 Workflow Checkpoint，支持中断恢复与状态追踪。

Checkpoint 采用分层存储策略：

- Recovery Checkpoint
- Confirmation Checkpoint

Checkpoint 中会保存 `current_node` 和经过字段生命周期瘦身后的 workflow state。Recovery Script 重新投递任务后，系统会自动读取 Checkpoint，计算 `resume_from_node`，再通过 Graph 中的 `route_resume` 跳转到后续节点继续执行。

不同 Checkpoint 类型决定恢复行为：

- `CheckpointMode.RECOVERY`：允许 Resume，自动继续执行 Workflow。
- `CheckpointMode.CONFIRMATION`：表示 Workflow 已进入 Human Confirmation，不再自动 invoke Graph，而是继续等待用户确认。

恢复逻辑基于 `checkpoint_mode` 判断，而不是依赖节点名称判断。

并基于字段生命周期进行状态瘦身，避免长期保存无效运行时数据。

### 9.2 Workflow Recovery
为避免 Celery Worker 异常退出、容器重启等情况导致 Workflow 长时间停留在 `queued`、`running` 状态，项目提供了手动恢复脚本。

恢复脚本会：

- 扫描 PostgreSQL 中未完成的 Workflow；
- 查询 Redis Broker 队列中的待执行任务；
- 按 `workflow_id` 对队列中已存在的任务进行去重，避免重复投递；
- 对确认丢失的任务重新提交到 Celery；
- 将上一次中断执行的步骤标记为 `failed`，并记录恢复原因。

执行命令：

```bash
docker compose exec api uv run python -m scripts.requeue_stuck_workflows
```

执行后会列出待恢复任务，并要求人工确认后再进行重新投递。

Recovery Script 用于补偿 Worker 异常退出、容器重启等场景下的任务丢失问题。它只对确认不在 Redis Broker 队列中的 stuck workflow 重新提交 Celery，避免重复任务。

重新投递后不会简单从起始节点重跑。当前恢复链路为：

```text
Workflow Checkpoint
    ↓
Checkpoint Resume
    ↓
Resume Router
    ↓
从最近 Checkpoint 的后继节点继续执行
```

Resume 流程：

```mermaid
flowchart TD
    Crash["Worker Crash / Docker Compose Down"] --> RecoveryScript["Recovery Script"]
    RecoveryScript --> LoadCheckpoint["Load Checkpoint"]
    LoadCheckpoint --> ModeCheck{"checkpoint_mode"}
    ModeCheck -->|recovery| Resume["Compute resume_from_node"]
    Resume --> Router["Resume Router<br/>route_resume"]
    Router --> Continue["Continue Workflow"]
    ModeCheck -->|confirmation| SkipInvoke["Skip Invoke"]
    SkipInvoke --> Waiting["Waiting Human Confirmation"]
```

当前已验证的恢复场景包括 Celery Worker 异常退出、Docker Compose Down 和 Worker 重启。整体链路为：

```text
Checkpoint
    ↓
Recovery Script
    ↓
Resume
    ↓
Workflow Continue
```

因此项目已经具备基础 Workflow Crash Recovery 能力。

### 9.3 Workflow Cancellation

支持运行中任务取消。

状态流转：

```text
queued
    ↓
cancelled

running
    ↓
cancelling
    ↓
cancelled
```

实现机制：

- 用户取消后，`queued` 任务直接进入 `cancelled`。
- `running` 任务先进入 `cancelling`。
- Worker 在节点边界检查 Workflow 状态。
- 发现 `cancelling` 时抛出 `WorkflowCancelledException`，主动终止 Workflow。
- Workflow 最终进入 `cancelled`。

取消检查通过统一的 `trace_node` 装饰器触发，不需要在每个节点重复编写取消逻辑。

Cancellation Flow：

```mermaid
flowchart TD
    Running["running"] --> Cancelling["cancelling"]
    Cancelling --> Boundary["Node Boundary Check"]
    Boundary --> Exception["WorkflowCancelledException"]
    Exception --> Cancelled["cancelled"]
```


## 10. API / Usage Example

### Submit workflow

```bash
curl -X POST http://127.0.0.1:8010/career_agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "session_id": "session_001",
    "job_description": "这里放岗位 JD",
    "resume_text": "这里放补充简历文本"
  }'
```

返回中会包含 `workflow_id` 和初始状态 `queued`。

### Get workflow status / report

```bash
curl http://127.0.0.1:8010/career_agent/runs/{workflow_id}
```

该接口返回 workflow 状态、匹配分数、最终报告、错误信息和最新 confirmation 信息。

### Get history by user

```bash
curl "http://127.0.0.1:8010/career_agent/runs?user_id=user_001&limit=20"
```

### Get trace

```bash
curl http://127.0.0.1:8010/career_agent/runs/{workflow_id}/trace
```

trace 会按节点返回 `agent_steps`，并嵌入对应的 `tool_calls`。

节点级 trace 包含状态、开始时间、结束时间、耗时、输入摘要、输出摘要、错误信息、Token Usage 和 Model 信息。Tool 级 trace 包含工具名称、工具类型、调用状态、开始时间、结束时间、耗时和输入输出摘要。前端可基于这些 Trace 数据展示完整 Workflow 执行链路。

### Cancel workflow

```bash
curl -X POST http://127.0.0.1:8010/career_agent/cancel/{workflow_id}
```

`queued` 状态会直接进入 `cancelled`，`running` 状态会先进入 `cancelling`，再由 Worker 在节点边界终止执行并进入 `cancelled`。

### Human confirmation

```bash
curl -X POST http://127.0.0.1:8010/career_agent/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow_xxx",
    "confirmation_id": "confirm_xxx",
    "action": "approve"
  }'
```

`action` 可选值：

- `approve`
- `revise`
- `reject`

## 11. Design Notes / 设计说明

**为什么使用 LangGraph，而不是单次 Prompt**

求职分析不是单步文本生成。它包含 JD 解析、检索规划、RAG 工具调用、证据反思、简历画像、匹配评分、报告生成、记忆写入和人工确认。使用 LangGraph 可以把这些节点显式建模，并让每个节点的输入输出更容易追踪。

**为什么拆出 Strategy Planner**

不同 JD 的能力要求差异很大，固定按“前端、后端、AI”检索会丢失岗位语义。`plan_career_analysis` 会基于 JD requirement 动态生成检索维度，并额外加入 background 检索，用于补充教育经历、项目经历和候选人整体背景。

**为什么需要 Tool Registry**

Graph 节点只通过 `resume_rag_retriever` 这样的工具名发起调用，具体实现可以是默认 HTTP RAG，也可以是 `USE_MCP_TOOLS=true` 时的 MCP stdio 适配。这样可以减少 workflow 对具体工具实现的耦合。

**为什么设置 max_retry**

ReAct 反思可以提升证据补充能力，但无限循环会让任务不可控。当前默认 `max_retry=1`，表示允许一次有边界的补充检索，用于演示 Agentic RAG 的闭环而不过度复杂化。

**为什么记录 agent_steps / tool_calls**

Agent 失败时只看最终报告很难定位问题。项目将节点状态、开始时间、结束时间、耗时、输入摘要、输出摘要、LLM Token Usage、Model 信息和工具调用记录写入 PostgreSQL，面试官可以通过 trace API 看到一次 workflow 的实际执行路径。前端也可以基于这些数据做执行链路可视化展示。

## 12. Screenshots / Demo

### RAG Upload

![RAG Upload](docs/screenshots/rag-upload.png)

### RAG Chat

![RAG Chat](docs/screenshots/rag-chat.png)

### JD Analysis Submit

![JD Analysis Submit](docs/screenshots/agent-submit.png)

### Agent Report

![Agent Report](docs/screenshots/agent-report.png)
![Agent Report](docs/screenshots/agent-report1.png)

### Agent Trace

![Agent Trace](docs/screenshots/agent-trace.png)

### Agent Checkpoint Resume

![Agent Checkpoint Resume](docs/screenshots/agent-checkpoint-resume.png)

## 13. Current Limitations / 当前边界

- 这是个人独立项目，不是生产级高可用平台。
- 当前是本地 / Docker Compose 演示部署，没有多副本部署、自动扩缩容或高可用配置。
- 本仓库不实现 RAG ingestion、embedding、hybrid search、rerank 或 ChromaDB 存储，这些能力属于外部 `ai-rag-knowledge-base-backend`。
- MCP 当前只是围绕 `resume_rag_retriever` 的基础可选适配层，不是完整多工具 MCP 生态。
- 当前没有认证、权限、限流和多租户隔离，不建议直接暴露到公网。
- 当前没有完整评测体系，也没有大规模 benchmark。
- 仓库目前没有独立 `tests/` 目录，测试覆盖仍需补充。
- 没有真实线上用户流量，也不会在 `approve` 后自动执行真实投递或邮件发送。

## 14. Roadmap / 后续计划

- 增加 Agent / RAG 报告质量的固定评测样例。
- 补充 LangSmith 或类似 tracing dashboard 的接入说明。
- 将 `schemas/execution_plan.py` 接入 planner 输出校验。
- 增加认证、权限和基础限流。
- 完善 Celery retry和 dead-letter 处理。
- 补充三仓库联调部署文档。

## 15. Security Notes / 安全说明

- API keys 应只存放在本地 `.env` 中。
- `.env` 不应提交到 Git 仓库。
- `.env.example` 应只包含占位符，不应包含真实 key、token 或密码。
- 如果曾经把真实 key 写入示例文件或提交历史，应立即轮换该 key。
- 当前 CORS 仅配置了本地前端地址，项目也没有认证层，不应直接作为公网服务运行。
