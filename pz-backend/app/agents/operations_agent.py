"""运营分析 Agent - 数据统计与运营建议"""
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Order, H5User, Companion
from sqlalchemy import func
from datetime import datetime, timedelta
from .base import BaseAgent


class OperationsAgent(BaseAgent):
    """运营分析 Agent：分析业务数据，提供运营建议"""

    def __init__(self):
        super().__init__("operations")

    def _default_system_prompt(self) -> str:
        return (
            "你是医疗陪诊平台的运营数据分析师。你可以：\n"
            "1. 分析订单数据（总量、状态分布、趋势）\n"
            "2. 分析用户数据（注册量、活跃度）\n"
            "3. 分析陪诊师数据（工作量、效率）\n"
            "4. 提供运营优化建议\n\n"
            "基于客观数据给出分析结论，数据用具体数字说话。"
        )

    def _collect_stats(self) -> dict:
        """收集运营统计数据"""
        db = SessionLocal()
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)

            # 订单统计
            total_orders = db.query(func.count(Order.id)).scalar() or 0
            today_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= today
            ).scalar() or 0

            status_distribution = {}
            for state in ["待支付", "待服务", "已完成", "已取消"]:
                count = db.query(func.count(Order.id)).filter(
                    Order.trade_state == state
                ).scalar() or 0
                status_distribution[state] = count

            # 用户统计
            total_users = db.query(func.count(H5User.id)).scalar() or 0
            new_users_week = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= week_ago
            ).scalar() or 0

            # 陪诊师统计
            total_companions = db.query(func.count(Companion.id)).filter(
                Companion.active == 1
            ).scalar() or 0

            return {
                "total_orders": total_orders,
                "today_orders": today_orders,
                "status_distribution": status_distribution,
                "total_users": total_users,
                "new_users_week": new_users_week,
                "total_companions": total_companions,
            }
        finally:
            db.close()

    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理运营分析查询"""
        stats = self._collect_stats()

        stats_text = (
            f"【订单数据】总订单：{stats['total_orders']}，今日新增：{stats['today_orders']}\n"
            f"订单分布：{stats['status_distribution']}\n"
            f"【用户数据】总用户：{stats['total_users']}，近7日新增：{stats['new_users_week']}\n"
            f"【陪诊师】总数：{stats['total_companions']}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "用户查询：{input}\n\n当前数据：\n{stats}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        reply = await chain.ainvoke({
            "input": user_input,
            "stats": stats_text,
        })

        return {
            "reply": reply,
            "meta_data": {
                "agent_type": "operations",
                "stats": stats,
            },
        }
