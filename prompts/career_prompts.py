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

请从下面的简历文本中提取候选人的能力画像。

要求：
1. 只输出 JSON
2. 不要输出 Markdown
3. 不要添加解释
4. 不要脑补简历中没有的信息
5. 每个技能尽量附带 evidence

简历文本：
{resume_text}

请严格按照以下 JSON 结构输出：

{{
  "frontend_skills": [
    {{
      "skill": "技能名称",
      "evidence": "简历中的证据"
    }}
  ],
  "backend_skills": [
    {{
      "skill": "技能名称",
      "evidence": "简历中的证据"
    }}
  ],
  "ai_skills": [
    {{
      "skill": "技能名称",
      "evidence": "简历中的证据"
    }}
  ],
  "infra_skills": [
    {{
      "skill": "技能名称",
      "evidence": "简历中的证据"
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

岗位能力要求：
{jd_analysis}

候选人能力画像：
{resume_profile}

请严格输出：

{{
  "match_score": 0,
  "matched_skills": [
    {{
      "skill": "",
      "evidence": ""
    }}
  ],
  "missing_skills": [],
  "strengths": [],
  "risks": [],
  "summary": ""
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
