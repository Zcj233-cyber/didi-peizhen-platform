"""AI Agent 基类"""
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from app.database import SessionLocal
from app.agent_models import AgentConfig


class BaseAgent(ABC):
    """Agent 基类，所有 Agent 继承此类"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.config = self._load_config()
        self.llm = self._init_llm()

    def _load_config(self) -> dict:
        """从数据库加载配置，不存在则返回默认值"""
        db = SessionLocal()
        try:
            cfg = db.query(AgentConfig).filter(
                AgentConfig.agent_type == self.agent_type
            ).first()
            if cfg and cfg.enabled:
                return {
                    "system_prompt": cfg.system_prompt or "",
                    "temperature": cfg.temperature or 0.7,
                    "max_tokens": cfg.max_tokens or 2048,
                    "enabled": True,
                    "model_name": cfg.model_name or DEEPSEEK_MODEL,
                }
        finally:
            db.close()
        return {
            "system_prompt": self._default_system_prompt(),
            "temperature": 0.7,
            "max_tokens": 2048,
            "enabled": True,
            "model_name": DEEPSEEK_MODEL,
        }

    def _init_llm(self) -> ChatOpenAI:
        """初始化 DeepSeek LLM"""
        return ChatOpenAI(
            model=self.config["model_name"],
            temperature=self.config["temperature"],
            max_tokens=self.config["max_tokens"],
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    @abstractmethod
    def _default_system_prompt(self) -> str:
        """子类必须提供默认系统提示词"""
        pass

    @abstractmethod
    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理用户输入并返回结果"""
        pass

    def _build_prompt(self, user_input: str, context: dict = None) -> list:
        """构建消息列表"""
        messages = [{"role": "system", "content": self.config["system_prompt"]}]
        if context and "history" in context:
            for msg in context["history"]:
                messages.append(msg)
        messages.append({"role": "user", "content": user_input})
        return messages
