"""AI Agent 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


class AgentChatRequest(BaseModel):
    """Agent 聊天请求"""
    message: str = Field(..., min_length=1, max_length=2000)
    agent_type: str = "auto"
    conversation_id: Optional[str] = ""


class TriageRequest(BaseModel):
    """分诊推荐请求"""
    symptoms: str = Field(..., min_length=1, max_length=1000)
    patient_age: Optional[int] = 0
    patient_gender: Optional[str] = ""


class AgentConfigUpdate(BaseModel):
    """Agent 配置更新"""
    agent_type: str
    enabled: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class AgentTaskParams(BaseModel):
    """任务列表查询参数"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    agent_type: Optional[str] = ""
    status: Optional[str] = ""


class AgentConversationParams(BaseModel):
    """会话列表查询参数"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    agent_type: Optional[str] = ""


class VisitPlanRequest(BaseModel):
    """就医规划请求"""
    symptoms: str = Field(..., min_length=1, max_length=1000, description="症状描述")
    patient_age: Optional[int] = Field(default=0, ge=0, le=150, description="患者年龄")
    patient_gender: Optional[str] = Field(default="", max_length=10, description="患者性别")
    city: Optional[str] = Field(default="", max_length=50, description="城市")
    lat: Optional[float] = Field(default=None, description="纬度")
    lng: Optional[float] = Field(default=None, description="经度")
    user_id: Optional[int] = Field(default=0, description="用户ID")
