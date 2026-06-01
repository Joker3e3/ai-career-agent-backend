ANALYZE_JD_PROMPT = """
你是一个通用岗位 JD 分析助手。

请从下面的岗位 JD 中，提取岗位事实信息。

要求：
1. 不要评价候选人
2. 不要生成学习建议
3. 只分析岗位本身
4. 只输出 JSON
5. 不要输出 Markdown
6. 不要添加解释
7. 不要假设岗位一定是技术岗
8. requirements 应该根据 JD 动态生成能力域
9. dimension 表示能力域，不要太细，也不要太泛
10. keywords 表示该能力域下的具体技能、工具、关键词或经验要求
11. priority 只能是 high / medium / low

能力域示例：
- 技术岗可以是：前端开发、后端开发、AI工程、工程化部署、数据分析、项目经验
- 人事岗可以是：招聘执行、员工关系、薪酬绩效、组织协调
- 行政岗可以是：行政协调、办公事务、资产管理、会议支持
- 销售岗可以是：客户开发、商务沟通、销售转化、客户维护
- 产品岗可以是：需求分析、产品设计、项目推进、用户研究

注意：
- 不要把具体技能直接当成 dimension，例如不要输出 “RAG项目经验” 或 “Vue经验”
- 应该输出 “AI工程” + keywords ["RAG", "Agent", "LangGraph"]
- 应该输出 “前端开发” + keywords ["Vue"]
- 应该输出 “后端开发” + keywords ["FastAPI"]

岗位 JD：
{job_description}

请严格按照以下 JSON 结构输出：

{{
  "role_title": "岗位名称",
  "role_category": "岗位类别，例如 tech / hr / admin / sales / product / finance / operation / other",
  "requirements": [
    {{
      "dimension": "能力域名称，例如 前端开发 / 后端开发 / AI工程 / 招聘执行 / 行政协调 / 客户开发",
      "priority": "high",
      "keywords": ["关键词1", "关键词2"],
      "description": "该能力域在岗位中的含义"
    }}
  ],
  "responsibilities": ["核心职责"],
  "background_requirements": ["学历、年限、行业、证书等背景要求"]
}}
"""


EXTRACT_RESUME_PROMPT = """
你是一个专业的 AI 简历分析助手。

请根据下面的 RAG 检索证据，提取候选人的能力画像。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 不要脑补证据中没有的信息
5. 每个技能必须附带 evidence
6. evidence 必须来自提供的 RAG 检索证据
7. 如果某类能力没有证据，返回空数组 []
8. frontend/backend/ai/infra skills 必须来自技能证据或补充简历文本。
9. education 可以来自背景证据。
10. projects 可以来自技能证据或背景证据。
11. 不要把 education 当成技能 evidence。

技能证据：
{skill_evidence}

背景证据：
{background_evidence}

补充简历文本：
{resume_text}

请严格按照以下 JSON 结构输出：

{{
  "frontend_skills": [
    {{
      "skill": "技能名称",
      "evidence": "证据原文"
    }}
  ],
  "backend_skills": [
    {{
      "skill": "技能名称",
      "evidence": "证据原文"
    }}
  ],
  "ai_skills": [
    {{
      "skill": "技能名称",
      "evidence": "证据原文"
    }}
  ],
  "infra_skills": [
    {{
      "skill": "技能名称",
      "evidence": "证据原文"
    }}
  ],
  "projects": [
    {{
      "name": "项目名称",
      "description": "项目描述",
      "skills": ["相关技能"]
    }}
  ],
  "education": "",
  "summary": ""
}}
"""


MATCH_JOB_PROMPT = """
你是一个专业的 AI 求职匹配分析助手。

请根据：

1. 岗位能力要求
2. 候选人简历能力画像

分析候选人与岗位的匹配程度。

要求：

1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 不要脑补简历中没有的信息
5. 所有匹配技能必须附带 evidence
6. match_score 范围 0-100
7. matched_skills 只能来自候选人能力画像中的明确 evidence
8. 如果岗位要求某技能，但候选人能力画像中没有证据，必须放入 missing_skills
9. risks 中要说明关键缺口

岗位能力要求：
{jd_analysis}

候选人能力画像：
{resume_profile}

请严格输出：

{{
  "match_score": 0,
  "matched_skills": [
    {{
      "skill": "匹配技能",
      "evidence": "候选人能力画像中的证据"
    }}
  ],
  "missing_skills": ["缺失技能"],
  "strengths": ["候选人优势"],
  "risks": ["候选人风险或不足"],
  "summary": "整体匹配结论"
}}
"""


GENERATE_LEARNING_PLAN_PROMPT = """
你是一个 AI 求职学习规划助手。

请根据岗位要求、候选人能力画像、匹配结果和历史分析记录，生成个性化学习路线。

要求：
1. 只输出 Markdown
2. 学习路线要具体
3. 优先补齐 missing_skills
4. 不要泛泛而谈
5. 如果历史记录中反复出现同一短板，请提高优先级

岗位要求：
{jd_analysis}

候选人能力画像：
{resume_profile}

匹配结果：
{match_result}

历史分析记录：
{memories}

请输出：
- 当前短板总结
- 7 天学习路线
- 项目补强建议
- 面试准备重点
"""


GENERATE_INTERVIEW_TIPS_PROMPT = """
你是一个 AI 求职面试辅导助手。

请根据岗位要求、候选人能力画像、匹配结果和历史分析记录，生成针对该岗位的面试准备建议。

要求：
1. 只输出 Markdown
2. 建议要具体，不要泛泛而谈
3. 优先围绕 matched_skills 准备项目表达
4. 对 missing_skills 给出补救话术
5. 如果历史记录中反复出现同一短板，请提醒重点补强
6. 不要编造候选人没有的经历

岗位要求：
{jd_analysis}

候选人能力画像：
{resume_profile}

匹配结果：
{match_result}

历史分析记录：
{memories}

请输出：
- 面试重点准备方向
- 项目讲解重点
- 可能被追问的问题
- 短板补救话术
"""


GENERATE_COVER_LETTER_PROMPT = """
你是一个专业的求职文案助手。

请根据岗位要求、候选人能力画像和匹配结果，生成一份简短、真实、有针对性的中文投递邮件草稿。

要求：
1. 只输出邮件正文
2. 不要编造简历中没有的经历
3. 突出 matched_skills 中有 evidence 的能力
4. 对 missing_skills 不要假装已经掌握，可以表达正在补强
5. 语气专业、简洁

岗位要求：
{jd_analysis}

候选人能力画像：
{resume_profile}

匹配结果：
{match_result}
"""


BUILD_RETRIEVAL_QUERIES_PROMPT = """
你是一个 RAG Query Builder。

你的任务不是重新分析岗位，也不是重新规划能力维度。

你的任务是根据 execution_plan 中已经确定的 retrieval_dimensions，
为每个检索维度生成一个适合 RAG 检索候选人简历的 query。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 每个 retrieval_dimension 必须生成且只能生成一个 query，queries 数组长度必须等于 retrieval_dimensions 数量。
5. 每个 query 必须来自 execution_plan.retrieval_dimensions
6. 不要新增 execution_plan 中不存在的能力维度
7. 必须保留 background 维度
8. query 使用自然语言表达，适合向量检索
9. keywords 直接来自对应 retrieval_dimension.keywords，可以少量补充同义词，但不要偏离原维度

execution_plan：
{execution_plan}

请严格按照以下 JSON 结构输出：

{{
  "queries": [
    {{
      "dimension": "前端开发",
      "query": "寻找候选人是否具备前端开发经验，特别是 Vue 项目、页面开发、组件开发和前后端交互经验。",
      "keywords": ["Vue", "前端开发", "页面开发", "组件"]
    }},
    {{
      "dimension": "background",
      "query": "寻找候选人的教育经历、工作经历、项目概述、个人背景和整体求职优势。",
      "keywords": ["教育经历", "学历", "工作经历", "项目经历", "个人背景", "求职优势"]
    }}
  ]
}}
"""


REFLECT_EVIDENCE_PROMPT = """
你是一个 ReAct 风格的 Agentic RAG 反思助手。

你的任务是根据 execution_plan、query_plan 和当前 evidence，
判断当前证据是否足以支持后续简历能力分析。

如果证据足够，输出 decision="continue"。

如果证据不足，输出 decision="act"，并从 available_tools 中选择一个工具继续获取证据。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. decision 只能是 "continue" 或 "act"
5. 如果 decision="continue"，tool_name 和 tool_input 必须为 null
6. 如果 decision="act"，tool_name 必须来自 available_tools
7. 当前 available_tools 只有 resume_rag_retriever
8. 如果需要继续检索，tool_input.query 必须换一种表达方式，避免重复 query_plan 中已有 query
9. 优先检查 execution_plan.retrieval_dimensions 中 priority 为 high 的维度
10. background 维度不参与技能匹配，只用于简历画像、求职自我介绍和 Cover Letter
11. 不要为了补全背景信息而频繁调用工具；只有关键匹配证据不足时才 action
12. 如果 retry_count 已达到 max_retry，必须 decision="continue"

execution_plan:
{execution_plan}

query_plan:
{query_plan}

当前 skill_evidence:
{skill_evidence}

当前 background_evidence:
{background_evidence}

available_tools:
{available_tools}

retry_count:
{retry_count}

max_retry:
{max_retry}

请严格按照以下 JSON 结构输出：

{{
  "decision": "act",
  "thought": "说明当前证据是否足够，以及为什么需要或不需要调用工具",
  "tool_name": "resume_rag_retriever",
  "tool_input": {{
    "query": "用于补充检索的自然语言 query",
    "keywords": ["关键词1", "关键词2"]
  }}
}}
"""
