from langchain_openai import ChatOpenAI
from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

json_llm = ChatOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model=DEEPSEEK_MODEL,
    temperature=0.2,
    model_kwargs={"response_format": {"type": "json_object"}},
)


text_llm = ChatOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model=DEEPSEEK_MODEL,
    temperature=0.2,
)