"""Agent 编排器 - 统一入口，关键词路由 + 单一Agent处理"""
import uuid
from datetime import datetime
from app.database import SessionLocal
from app.agent_models import AgentConversation, AgentMessage, AgentTask
from .triage_agent import TriageAgent
from .customer_service import CustomerServiceAgent
from .order_assistant import OrderAssistantAgent
from .operations_agent import OperationsAgent


def generate_uuid() -> str:
    return uuid.uuid4().hex[:16]


# 关键词 → Agent类型映射（替代调度中心Agent）
KEYWORD_ROUTES = {
    "triage": ["症状", "咳嗽", "发烧", "头痛", "肚子", "科室", "医院", "挂", "分诊", "推荐科室"],
    "order_assistant": ["订单", "预约", "取消", "改约", "催", "单号", "PZ", "查"],
    "operations": ["订单数量", "统计", "数据", "多少", "增长", "分析", "报表", "趋势"],
}


def route_intent(message: str) -> str:
    """关键词匹配意图，替代原来的调度中心Agent"""
    for intent, keywords in KEYWORD_ROUTES.items():
        for kw in keywords:
            if kw in message:
                return intent
    return "customer_service"


class AgentOrchestrator:
    """Agent 编排器 - 单一Agent路由"""

    def __init__(self):
        self.agents = {
            "triage": TriageAgent(),
            "customer_service": CustomerServiceAgent(),
            "order_assistant": OrderAssistantAgent(),
            "operations": OperationsAgent(),
        }

    async def chat(
        self,
        message: str,
        agent_type: str = "auto",
        user_id: int = 0,
        user_name: str = "",
        conversation_id: str = "",
    ) -> dict:
        """统一聊天入口"""
        db = SessionLocal()
        try:
            # 1. 获取或创建会话
            conv = None
            if conversation_id:
                conv = db.query(AgentConversation).filter(
                    AgentConversation.conversation_id == conversation_id
                ).first()

            if not conv:
                conversation_id = generate_uuid()
                conv = AgentConversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    user_name=user_name,
                    agent_type=agent_type,
                    title=message[:50],
                    status=1,
                    source="h5",
                )
                db.add(conv)
                db.commit()

            # 2. 获取对话历史
            history = db.query(AgentMessage).filter(
                AgentMessage.conversation_id == conversation_id
            ).order_by(AgentMessage.created_at).all()
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in history[-6:]
            ]

            # 3. 意图识别（关键词匹配，不调大模型）
            target_agent_type = agent_type
            if agent_type == "auto":
                target_agent_type = route_intent(message)
                if target_agent_type not in self.agents:
                    target_agent_type = "customer_service"
                conv.agent_type = target_agent_type
                db.commit()

            # 4. 保存用户消息
            db.add(AgentMessage(
                conversation_id=conversation_id,
                role="user",
                content=message,
                content_type="text",
            ))

            # 5. 创建任务记录
            task_id = generate_uuid()
            task = AgentTask(
                task_id=task_id,
                agent_type=target_agent_type,
                user_id=user_id,
                conversation_id=conversation_id,
                task_type=f"{target_agent_type}_inquiry",
                input_data={"message": message},
                status="processing",
                started_at=datetime.now(),
            )
            db.add(task)
            db.commit()

            # 6. 调用Agent
            context = {"user_id": user_id, "user_name": user_name, "history": history_messages}
            agent = self.agents.get(target_agent_type)
            result = await agent.process(message, context)
            reply = result.get("reply", "")
            meta_data = result.get("meta_data", {})

            # 7. 保存回复
            db.add(AgentMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=reply,
                content_type="text",
                meta_data=meta_data,
            ))

            # 8. 完成任务
            task.status = "completed"
            task.output_data = result
            task.completed_at = datetime.now()
            db.commit()

            return {
                "reply": reply,
                "agent_type": target_agent_type,
                "conversation_id": conversation_id,
                "meta_data": meta_data,
            }

        except Exception as e:
            db.rollback()
            return {
                "reply": "抱歉，我暂时无法处理您的问题，请稍后再试。",
                "agent_type": "error",
                "conversation_id": conversation_id or "",
                "meta_data": {"error": str(e)},
            }
        finally:
            db.close()

    async def triage_recommend(
        self, symptoms: str, patient_age: int = 0, patient_gender: str = "",
    ) -> dict:
        """分诊推荐（独立入口）"""
        agent = self.agents["triage"]
        context = {"patient_age": patient_age, "patient_gender": patient_gender}
        result = await agent.process(symptoms, context)
        return result.get("meta_data", {})

    def get_overview(self) -> dict:
        """运营数据总览"""
        db = SessionLocal()
        try:
            from app.models import Order, H5User
            from app.agent_models import AgentConversation, AgentTask, AgentConfig, FAQ

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            return {
                "total_orders": db.query(Order).count(),
                "total_users": db.query(H5User).count(),
                "total_conversations": db.query(AgentConversation).count(),
                "today_tasks": db.query(AgentTask).filter(AgentTask.created_at >= today).count(),
                "faq_count": db.query(FAQ).filter(FAQ.enabled == 1).count(),
                "success_rate": 0,
                "enabled_agents": db.query(AgentConfig).filter(AgentConfig.enabled == 1).count(),
            }
        finally:
            db.close()
