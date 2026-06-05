# AI Career Agent

AI Career Agent 是一个面向求职场景的后端 Agent 工程项目。它接收用户的岗位 JD、用户标识、会话标识和补充简历文本，结合外部简历 RAG 服务检索到的候选人证据，生成岗位匹配分析、学习或面试建议、投递邮件草稿，并进入人工确认流程。

这个项目的重点不是做一个一次性 Prompt，而是把 JD 分析、检索规划、工具调用、ReAct 反思、长期记忆、异步任务、人工确认和可观测性串成一个可运行的 Agent Workflow。

## 项目简介

项目解决的问题：

- 将岗位 JD 拆解为可检索、可评估的能力域。
- 从候选人简历知识库中检索与岗位能力相关的证据。
- 基于证据生成简历画像、岗位匹配结果和求职建议。
- 在生成投递邮件草稿后进入 Human Confirmation，不直接执行真实投递。
- 记录 Agent 节点、工具调用、运行状态和确认结果，方便复盘和调试。

用户输入：

- `user_id`
- `session_id`
- `job_description`
- `resume_text`

系统输出：

- 异步任务的 `workflow_id` 和运行状态。
- 最终分析报告 `final_report`。
- 岗位匹配分数 `match_score`。
- 学习路线或面试建议。
- Cover Letter 草稿。
- `confirmation_id`，用于用户确认 `approve` / `revise` / `reject`。
- Agent Trace，包括节点执行记录和工具调用记录。

为什么要做这个项目：

这个项目用于学习和展示 AI Agent 工程中更接近真实业务的几个关键能力：让 Agent 先规划再检索，用工具补充证据，用 ReAct 判断是否需要继续行动，用长期记忆持续更新用户画像，用 Celery 承接长任务，并用 Trace 记录 Agent 的执行过程。

## 核心能力

- **JD 能力域分析**：通过 LLM 将岗位 JD 解析为 `role_title`、`role_category`、能力要求、职责和背景要求。能力域不是固定写死为前端、后端、AI，而是根据 JD 动态生成。
- **Strategy Planner**：`plan_career_analysis` 根据 JD 分析结果生成 `execution_plan`，包括检索维度、背景检索维度、重试策略和输出要求。
- **Tool Registry & Tool Calling**：`ToolRegistry` 注册 `resume_rag_retriever`，Graph 通过 `call_tool` 调用工具，而不是直接绑定具体函数。
- **ReAct Retrieval Loop**：`reflect_evidence` 让 LLM 基于当前 evidence 和 available tools 判断 `continue` 或 `act`；当需要补充证据时，执行工具后回到反思节点。
- **Resume RAG Retrieval**：通过 `RAG_SERVICE_URL/retrieve_evidence` 调用外部 RAG 服务，按能力域检索候选人简历证据。
- **Long-Term Memory**：PostgreSQL 中保存 `application_history`、`profile_summary`、`preference`，后续学习计划、面试建议和 Cover Letter 会使用这些记忆。
- **Human Confirmation**：生成报告和投递邮件草稿后，Workflow 进入 `waiting_human_confirmation`，等待用户确认。
- **Celery 异步执行**：FastAPI 提交任务后立即返回 `workflow_id`，实际 Agent Workflow 在 Celery Worker 中执行。
- **MCP 可选工具接入**：通过 `USE_MCP_TOOLS=true` 将 RAG 工具切换为 MCP stdio 调用路径。
- **Trace / Observability**：节点执行和工具调用分别写入 `agent_steps`、`tool_calls`，并通过 API 查询完整 Trace。

## 技术栈

**Backend**

- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn

**Agent Framework**

- LangGraph
- LangChain OpenAI-compatible Chat Model
- ReAct-style reflection loop
- Tool Registry / Tool Calling

**Database**

- PostgreSQL
- SQLAlchemy ORM
- `agent_runs`
- `agent_steps`
- `tool_calls`
- `human_confirmations`
- `user_memories`

**Middleware**

- Redis
- Celery Broker
- Celery Result Backend
- Workflow runtime state
- Confirmation state

**AI / LLM**

- DeepSeek-compatible OpenAI API client
- JSON mode LLM for structured outputs
- Text LLM for report, learning plan, interview tips and cover letter
- External Resume RAG Service

**Tooling**

- uv
- python-dotenv
- requests
- MCP Python SDK

## 系统架构

```mermaid
flowchart LR
    Client[API Client] --> FastAPI[FastAPI]

    FastAPI --> AnalyzeAPI[POST /career_agent/analyze]
    FastAPI --> ConfirmAPI[POST /career_agent/confirm]
    FastAPI --> QueryAPI[Run / Trace Query APIs]

    AnalyzeAPI --> CareerService[Career Analysis Service]
    CareerService -->|create queued run| PostgreSQL[(PostgreSQL)]
    CareerService -->|delay task| RedisBroker[(Redis Broker)]

    RedisBroker --> Celery[Celery Worker]
    Celery --> LangGraph[LangGraph Career Agent]

    LangGraph --> ToolRegistry[Tool Registry]
    ToolRegistry --> RAGTool[resume_rag_retriever]

    RAGTool -->|default HTTP| RAGService[External RAG Service]
    RAGTool -. USE_MCP_TOOLS=true .-> MCPClient[MCP Client]
    MCPClient -. stdio .-> MCPServer[MCP Server]
    MCPServer -. HTTP .-> RAGService

    LangGraph -->|runs / steps / tool_calls / memories / confirmations| PostgreSQL
    LangGraph -->|workflow state / confirmation state| RedisState[(Redis State)]

    ConfirmAPI --> RedisState
    ConfirmAPI --> PostgreSQL
    QueryAPI --> PostgreSQL
```

## Agent Workflow

以下流程基于 `agents/career_graph.py` 中实际 `StateGraph` 代码生成。

```mermaid
flowchart TD
    START([START]) --> load_memory[load_memory]
    load_memory --> analyze_jd[analyze_jd]
    analyze_jd --> plan_career_analysis[plan_career_analysis]
    plan_career_analysis --> build_retrieval_queries[build_retrieval_queries]
    build_retrieval_queries --> retrieve_resume_evidence[retrieve_resume_evidence]
    retrieve_resume_evidence --> reflect_evidence[reflect_evidence]

    reflect_evidence -->|decision=act and retry_count < max_retry and tool_name exists| execute_react_action[execute_react_action]
    execute_react_action --> reflect_evidence

    reflect_evidence -->|continue or max retry reached| extract_resume_profile[extract_resume_profile]
    extract_resume_profile --> match_job[match_job]

    match_job -->|match_score >= 80| generate_interview_tips[generate_interview_tips]
    match_job -->|match_score < 80| generate_learning_plan[generate_learning_plan]

    generate_interview_tips --> generate_cover_letter[generate_cover_letter]
    generate_learning_plan --> generate_cover_letter

    generate_cover_letter --> generate_report[generate_report]
    generate_report --> save_memory[save_memory]
    save_memory --> create_confirmation[create_confirmation]
    create_confirmation --> END([END])

    subgraph Confirm Workflow
        CSTART([START]) --> confirm_node[confirm_node]
        confirm_node --> CEND([END])
    end
```

## 核心设计

### JD-driven Strategy Planner

设计动机：岗位 JD 的能力要求不一定是技术岗，也不应该固定拆成前端、后端、AI 等模板。系统先让 LLM 提取 JD 的能力域、优先级、关键词、职责和背景要求，再由 `plan_career_analysis` 生成执行计划。

实现方式：`analyze_jd` 输出 `JDAnalysis`；`plan_career_analysis` 将 `requirements` 转换为 `retrieval_dimensions`，并额外加入 `background` 检索维度，用于教育经历、项目概述、整体背景和求职优势。

价值：后续 RAG 查询不是对整份 JD 做一次粗粒度检索，而是围绕岗位能力域逐项检索证据。

### Tool Registry & Tool Calling

设计动机：Agent 节点不直接依赖具体工具函数，而是通过工具名称调用，便于后续扩展更多工具或切换工具实现。

实现方式：`tools/tool_registry.py` 定义 `ToolDefinition` 和 `ToolRegistry`；`tools/career_tools.py` 注册 `resume_rag_retriever`；`tools/tool_executor.py` 通过 `call_tool(tool_name, **kwargs)` 执行工具。

价值：Graph 只关心要调用哪个工具，具体是 HTTP RAG 还是 MCP RAG 由注册阶段决定。

### ReAct-style Reflection Loop

设计动机：RAG 首次检索结果可能不足以支撑岗位匹配结论，Agent 需要判断是否继续行动，而不是盲目生成报告。

实现方式：`reflect_evidence` 基于 `execution_plan`、`query_plan`、当前 evidence、available tools、`retry_count` 和 `max_retry` 生成 `ReactDecision`。当 decision 为 `act` 时，`execute_react_action` 调用工具补充 evidence，并回到 `reflect_evidence`。

价值：系统具备一个有限次数的 ReAct 检索闭环。默认 `max_retry=1`，避免无限 Agent Loop。

### Long-Term Memory

设计动机：求职分析不是孤立任务，历史申请记录、长期能力画像和偏好会影响学习计划、面试建议和投递文案。

实现方式：`load_memory` 从 `user_memories` 加载最近的 `application_history`、`profile_summary` 和 `preference`；`save_memory` 保存本次分析历史，并调用 LLM 更新长期画像和偏好摘要。

价值：后续生成不只依赖当前 JD 和简历 evidence，也会参考用户过去反复出现的优势、短板和岗位方向。

### MCP Optional Adapter

设计动机：保留 MCP 工具接入层，方便将本地工具协议化，并学习 MCP Client / Server 的调用方式。

实现方式：默认情况下，`resume_rag_retriever` 通过 HTTP 调用外部 RAG 服务；当 `USE_MCP_TOOLS=true` 时，注册为 `retrieve_evidence_from_mcp_rag`，通过 stdio 启动 `mcp_server.py` 并调用 MCP Tool。

价值：当前 MCP 不是必需依赖，而是可选适配层。它让同一个 Tool Registry 名称可以切换不同工具后端。

### Observability & Trace

设计动机：Agent Workflow 多节点、多工具调用，如果没有 Trace，很难定位卡在哪个节点、调用了什么工具、输出了什么摘要。

实现方式：`trace_node` 装饰器记录节点开始、结束、耗时、状态、输入摘要和输出摘要；`trace_tool` 装饰器记录工具调用的输入、输出、耗时和错误。查询接口为 `/career_agent/runs/{workflow_id}/trace`。

价值：面试官或学习者可以从数据库和 API 看到 Agent 的实际执行路径，而不是只能看到最终报告。

### Celery Async Workflow

设计动机：岗位分析包含 LLM 调用、RAG 检索、反思循环和数据库写入，不适合由 HTTP 请求同步阻塞完成。

实现方式：`submit_career_analysis` 创建 `queued` 状态的 `agent_runs` 记录，并通过 `execute_career_analysis_task.delay(...)` 投递 Celery 任务；Worker 执行 `career_graph.invoke(...)`，并将运行状态更新为 `running`、`waiting_human_confirmation`。

价值：API 层可以快速返回 `workflow_id`，调用方再通过 Run 查询接口和 Trace 接口查看结果。

## 项目亮点

- **Agentic RAG**：RAG 是 Agent Workflow 中可调用的工具，而不是一次性拼接上下文。
- **ReAct**：Agent 会基于证据质量决定继续生成还是再次调用工具。
- **Tool Calling**：Graph 使用工具名和 Tool Registry 解耦具体实现。
- **Long-Term Memory**：历史申请、长期画像和偏好会影响后续建议和文案。
- **MCP**：提供可选 MCP stdio 工具适配，当前接入 `resume_rag_retriever`。
- **Celery**：长流程异步执行，API 返回 `workflow_id` 后由 Worker 处理。
- **Observability**：节点和工具调用均落库，可通过 Trace API 查询。
- **Human-in-the-loop**：投递邮件草稿生成后必须等待用户确认，不默认执行真实投递。

## 项目结构

```text
.
├── main.py                         # FastAPI 入口与核心 API
├── celery_app.py                   # Celery 应用配置
├── mcp_server.py                   # 可选 MCP Server
├── agents/
│   ├── career_graph.py             # LangGraph 主流程与确认流程
│   └── career/
│       ├── trace.py                # 节点与工具 Trace 装饰器
│       ├── trace_summary.py        # Trace 输入摘要
│       └── state_policy.py         # Workflow checkpoint 字段策略
├── tools/
│   ├── tool_registry.py            # Tool Registry
│   ├── tool_executor.py            # Tool Calling 入口
│   ├── career_tools.py             # 求职分析工具注册
│   ├── rag_evidence_tool.py        # HTTP RAG 工具
│   └── mcp_tools.py                # MCP 工具适配
├── services/
│   ├── career_analysis_service.py  # 异步任务提交与执行
│   ├── long_term_memory_service.py # 长期记忆
│   ├── workflow_state_service.py   # Redis Workflow State
│   ├── confirmation_service.py     # Redis Confirmation State
│   ├── agent_trace_service.py      # Trace 查询
│   └── agent_run_query_service.py  # Run 查询
├── database/
│   ├── models/                     # SQLAlchemy Models
│   ├── repositories/               # 数据访问层
│   ├── database.py                 # 数据库连接
│   └── init_db.py                  # 建表入口
├── schemas/                        # Pydantic 输出结构
├── prompts/                        # LLM Prompts
├── routers/                        # 查询路由
├── tasks/                          # Celery Tasks
├── config/                         # 环境变量与日志配置
└── llms/                           # LLM Client
```

## 安装与运行

### 环境要求

- Python 3.11+
- PostgreSQL
- Redis
- uv
- DeepSeek 或兼容 OpenAI Chat Completions 的模型服务
- 外部 Resume RAG Service，需要提供 `POST /retrieve_evidence`

### 安装依赖

```bash
uv sync
```

如果不使用 uv，也可以基于 `pyproject.toml` 手动安装依赖。

### 环境变量

在项目根目录创建 `.env`：

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/ai_career_agent

DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

RAG_SERVICE_URL=http://127.0.0.1:8000

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true

USE_MCP_TOOLS=false
LOG_LEVEL=INFO
WORKFLOW_STATE_TTL=86400
CONFIRMATION_TTL=86400
SESSION_MEMORY_TTL=2592000
```

### 数据库初始化

先创建 PostgreSQL 数据库，例如：

```bash
createdb ai_career_agent
```

然后初始化表结构：

```bash
uv run python -m database.init_db
```

当前仓库通过 SQLAlchemy `Base.metadata.create_all` 建表，尚未提供 Alembic migration 文件。

### Redis

本项目依赖 Redis 作为 Celery Broker、Celery Result Backend、Workflow State 和 Confirmation State。

本地启动：

```bash
redis-server
```

或使用 Docker：

```bash
docker run --name ai-career-agent-redis -p 6379:6379 -d redis:7
```

### FastAPI

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8010
```

服务启动后可访问：

```text
http://127.0.0.1:8010/docs
```

### Celery Worker

Windows 环境建议使用 `--pool=solo`：

```bash
uv run celery -A celery_app.celery_app worker --loglevel=INFO --pool=solo
```

Linux / macOS 可使用：

```bash
uv run celery -A celery_app.celery_app worker --loglevel=INFO
```

### MCP Server（可选）

默认 `USE_MCP_TOOLS=false`，工具会直接通过 HTTP 调用外部 RAG 服务。

如需走 MCP 适配层：

```env
USE_MCP_TOOLS=true
```

当前 MCP Client 会通过 stdio 启动：

```bash
uv run python mcp_server.py
```

也可以单独运行该命令用于调试 MCP Server。

### API 示例

提交分析任务：

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

查询运行详情：

```bash
curl http://127.0.0.1:8010/career_agent/runs/{workflow_id}
```

查询 Trace：

```bash
curl http://127.0.0.1:8010/career_agent/runs/{workflow_id}/trace
```

人工确认：

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

## 当前限制与 Future Work

- **不会真实投递申请**：当前只生成 Cover Letter 草稿并等待用户确认；`approve` 只记录确认结果，不会调用招聘网站或邮件发送接口。
- **MCP 当前为可选接入层**：目前 MCP 只封装了 `resume_rag_retriever`，不是完整的多工具 MCP 生态。
- **Dynamic Planner 未作为主流程实现**：当前主流程是 JD-driven Strategy Planner，不是通用 Dynamic Planner；`schemas/execution_plan.py` 尚未接入主流程校验。
- **RAG 服务不在本仓库内实现**：当前代码调用外部 `RAG_SERVICE_URL/retrieve_evidence`，没有包含简历向量库构建、索引和召回服务。
- **重试次数有限**：ReAct 检索闭环默认 `max_retry=1`，用于避免无限循环。
- **任务失败处理仍可增强**：`WorkflowStatus.FAILED` 已定义，但 Celery task 的失败状态落库处理还可以继续完善。
- **数据库迁移仍可增强**：依赖中包含 Alembic，但当前没有 migration 脚本。
- **测试覆盖仍可补充**：当前仓库未包含独立测试目录，后续可以补充 graph 节点、tool registry、trace、repository 和 API 的测试。

未来可以继续扩展：

- 增加真实投递或邮件发送 Connector，并放在 Human Confirmation 之后。
- 增加更多 MCP Tools，例如职位搜索、公司信息查询、面试题检索。
- 将 `ExecutionPlan` schema 接入 planner 校验。
- 将 RAG ingestion、向量库和检索服务纳入同一工程或提供独立部署说明。
- 增加 Agent Evals，用固定 JD 和简历样本评估匹配结果稳定性。
- 增加 Celery retry、失败落库、任务取消和 dead-letter 处理。

# 部署指南（Deployment）

## 1. 前置条件

- Docker
- Docker Compose
- 已启动的 Resume RAG Service

Career Agent 依赖外部 Resume RAG Service。启动本项目之前，请先启动 RAG 项目。

## 2. 环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

RAG_SERVICE_URL=http://host.docker.internal:8000

DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_career_agent

REDIS_HOST=redis
REDIS_PORT=6379

USE_MCP_TOOLS=False
LOG_LEVEL=INFO
```

- `DEEPSEEK_API_KEY`：DeepSeek 兼容 Chat Model 的 API Key。
- `DEEPSEEK_BASE_URL`：DeepSeek 兼容 OpenAI API 的 Base URL。
- `DEEPSEEK_MODEL`：Career Agent 使用的模型名称。
- `RAG_SERVICE_URL`：外部 Resume RAG Service 的 HTTP 地址。
- `DATABASE_URL`：FastAPI API 和 Celery Worker 使用的 PostgreSQL 连接地址。
- `REDIS_HOST`：Celery 和 Workflow State 服务使用的 Redis 主机名。
- `REDIS_PORT`：Celery 和 Workflow State 服务使用的 Redis 端口。
- `USE_MCP_TOOLS`：是否启用可选的 MCP 工具调用方式；保持 `False` 时，Career Agent 会直接通过 HTTP 调用 RAG Service。
- `LOG_LEVEL`：应用日志级别。

## 3. 构建并启动

```bash
docker compose up -d --build
```

该命令会启动：

- `api`
- `worker`
- `postgres`
- `redis`

## 4. 初始化数据库

首次启动后执行：

```bash
docker compose exec api uv run python -m database.init_db
```

数据库表初始化只需执行一次。

## 5. 访问服务

Career Agent API:

```text
http://localhost:8001
```

Swagger:

```text
http://localhost:8001/docs
```

## 6. 查看日志

查看 API 日志：

```bash
docker compose logs -f api
```

查看 Worker 日志：

```bash
docker compose logs -f worker
```

## 7. 停止服务

```bash
docker compose down
```

该命令会保留 PostgreSQL 数据。

## 8. 删除所有数据

```bash
docker compose down -v
```

该命令会删除 PostgreSQL Volume 和 Redis Volume。

下次启动后需要重新初始化数据库。

## 9. 部署架构

```text
Browser
    │
    ▼
Frontend (Vue)
localhost:5173
    │
    ▼
Career Agent API
localhost:8001
    │
    ├── PostgreSQL
    ├── Redis
    └── Celery Worker
            │
            ▼
Resume RAG Service
localhost:8000
```
