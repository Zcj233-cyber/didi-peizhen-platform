"""AI Agent 数据库模型"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, SmallInteger, JSON, func
from .database import Base


class AgentConversation(Base):
    """AI代理会话记录"""
    __tablename__ = "agent_conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), unique=True, nullable=False, comment="会话唯一ID")
    user_id = Column(Integer, default=0, comment="H5用户ID")
    user_name = Column(String(50), comment="用户昵称")
    agent_type = Column(String(100), nullable=False, comment="代理类型")
    title = Column(String(200), comment="会话标题")
    status = Column(SmallInteger, default=1, comment="状态 1进行中 2已完成 3已关闭")
    source = Column(String(30), default="h5", comment="来源")
    extra_data = Column(JSON, comment="额外数据")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AgentMessage(Base):
    """AI代理消息记录"""
    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色")
    content = Column(Text, nullable=False, comment="消息内容")
    content_type = Column(String(30), default="text", comment="内容类型")
    meta_data = Column(JSON, comment="元数据")
    created_at = Column(DateTime, default=func.now())


class AgentTask(Base):
    """AI代理任务记录"""
    __tablename__ = "agent_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, comment="任务唯一ID")
    agent_type = Column(String(100), nullable=False, comment="代理类型")
    user_id = Column(Integer, default=0, comment="触发用户ID")
    conversation_id = Column(String(64), comment="关联会话ID")
    task_type = Column(String(50), nullable=False, comment="任务类型")
    input_data = Column(JSON, comment="输入数据")
    output_data = Column(JSON, comment="输出数据")
    status = Column(String(20), default="pending", comment="状态")
    error_message = Column(Text, comment="错误信息")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AgentConfig(Base):
    """AI代理配置"""
    __tablename__ = "agent_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(30), unique=True, nullable=False, comment="代理类型")
    display_name = Column(String(50), comment="显示名称")
    enabled = Column(SmallInteger, default=1, comment="启用状态 1启用 0禁用")
    model_name = Column(String(100), default="deepseek-chat", comment="模型名称")
    temperature = Column(Float, default=0.70, comment="温度参数")
    max_tokens = Column(Integer, default=2048, comment="最大Token数")
    system_prompt = Column(Text, comment="系统提示词")
    extra_params = Column(JSON, comment="额外参数")
    updated_by = Column(Integer, default=0, comment="更新人")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AgentFeedback(Base):
    """AI客服评价"""
    __tablename__ = "agent_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), comment="会话ID")
    message_id = Column(Integer, comment="消息ID")
    user_id = Column(Integer, default=0, comment="用户ID")
    rating = Column(SmallInteger, default=0, comment="评分 1好评 2差评")
    feedback_text = Column(Text, comment="反馈内容")
    created_at = Column(DateTime, default=func.now())


class FAQ(Base):
    """常见问题知识库"""
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False, comment="问题")
    answer = Column(Text, nullable=False, comment="答案")
    category = Column(String(50), default="general", comment="分类")
    keywords = Column(String(500), comment="关键词")
    sort = Column(Integer, default=0, comment="排序")
    enabled = Column(SmallInteger, default=1, comment="启用状态")
    created_at = Column(DateTime, default=func.now())
