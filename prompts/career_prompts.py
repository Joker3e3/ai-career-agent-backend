ANALYZE_JD_PROMPT = """
你是一个 AI 求职分析助手。

请从下面的岗位 JD 中，提取岗位需要的能力要求。

要求：
1. 不要评价候选人
2. 不要生成学习建议
3. 只分析岗位本身
4. 输出简洁 Markdown

岗位 JD：
{job_description}

请严格按照以下 JSON 结构输出：

{{
  "role_title": "岗位名称",
  "required_skills": ["必备技能"],
  "preferred_skills": ["加分技能"],
  "frontend_skills": ["前端技能"],
  "backend_skills": ["后端技能"],
  "ai_skills": ["AI相关技能"],
  "infra_skills": ["工程化/部署/中间件技能"],
  "soft_skills": ["软技能"],
  "responsibilities": ["核心职责"]
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
你是一个 RAG 检索规划助手。

请根据岗位 JD 分析结果，生成用于检索候选人简历/项目经历的查询计划。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 每个 query 应该用于检索一个能力维度
5. query 使用自然语言表达，适合向量检索
6. keywords 使用关键词数组，适合 BM25 / Hybrid Search
7. queries 数组长度最大为 5
8. 除技能维度 query 外，必须生成一个 dimension 为 "background" 的 query，用于检索教育经历、个人背景、项目概述、整体经历、学历程度、毕业院校。
9. background query 不参与技能匹配，只用于生成简历画像、求职自我介绍和 cover letter。

岗位 JD 分析结果：
{jd_analysis}

请严格按照以下 JSON 结构输出：

{{
  "queries": [
    {{
      "dimension": "frontend",
      "query": "寻找候选人是否具备 Vue 前端项目经验，包括页面开发、组件化和前后端交互。",
      "keywords": ["Vue", "前端", "组件", "页面"]
    }},
    {{
      "dimension": "background",
      "query": "寻找候选人的教育经历、个人背景、项目概述和整体求职优势。",
      "keywords": ["教育经历", "学历", "项目经历", "个人背景", "求职优势"]
    }}
  ]
}}
"""


REFLECT_EVIDENCE_PROMPT = """
你是一个 Agentic RAG 反思助手。

请检查当前 RAG 检索结果是否足够支持后续简历能力分析。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 如果某个检索维度没有有效 evidence，生成 retry query
5. retry query 应该换一种表达方式，包含同义词或相关表达
6. 最多生成 3 个 retry query
7. 如果 evidence 已经足够，need_retry=false

原始 query_plan：
{query_plan}

当前 skill_evidence：
{skill_evidence}

请严格按照以下 JSON 结构输出：

{{
  "need_retry": true,
  "retry_queries": [
    {{
      "dimension": "ai_skills",
      "reason": "未找到 Agent 相关证据，需要尝试 LangGraph、智能体、工具调用等关键词",
      "retry_query": "寻找候选人是否具备智能体开发、LangGraph 工作流、工具调用或 Agent 项目经验。",
      "keywords": ["智能体", "LangGraph", "工具调用", "Agent", "工作流"]
    }}
  ]
}}
"""
