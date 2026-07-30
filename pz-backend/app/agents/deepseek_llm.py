"""DeepSeek LLM 封装"""
from langchain_openai import ChatOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


def create_deepseek_llm(temperature: float = 0.7, max_tokens: int = 2048) -> ChatOpenAI:
    """创建 DeepSeek LLM 实例"""
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )
