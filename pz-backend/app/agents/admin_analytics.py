"""深度分析 Agent - 多维业务分析与运营建议"""
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Order, H5User, Companion, Hospital
from app.agent_models import AgentFeedback, AgentConversation
from .base import BaseAgent


class AdminAnalyticsAgent(BaseAgent):
    """深度分析 Agent：多维分析业务数据，生成运营洞察"""

    def __init__(self):
        super().__init__("admin_analytics")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个医疗陪诊平台的资深数据分析师。根据业务数据，给出深度分析和可执行的运营建议。\n\n"
            "分析维度：\n"
            "1. 订单分析：各状态占比、趋势变化、异常波动\n"
            "2. 用户分析：增长趋势、用户活跃度\n"
            "3. 陪诊师分析：工作量分布、效率\n"
            "4. 医院分析：热门医院排名\n"
            "5. AI客服分析：咨询量、满意度\n\n"
            "要求：\n"
            "- 用数据说话，给出具体数字\n"
            "- 点出核心问题和机会\n"
            "- 给出可执行的运营建议\n\n"
            "请以JSON格式输出：\n"
            "- dimensions: 各维度分析列表（每项含 name, data, insight, suggestion）\n"
            "- key_findings: 核心发现列表\n"
            "- action_items: 建议行动项列表\n"
            "- summary: 分析总结"
        )

    def _collect_analytics(self) -> dict:
        """采集所有分析数据"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)

            # === 1. 订单深度分析 ===
            total = db.query(func.count(Order.id)).scalar() or 0

            # 近7天各状态分布
            week_orders = db.query(Order).filter(Order.created_at >= week_ago).all()
            week_status = {}
            for o in week_orders:
                week_status[o.trade_state] = week_status.get(o.trade_state, 0) + 1

            # 每日订单趋势（近7天）
            daily_orders = {}
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                cnt = db.query(func.count(Order.id)).filter(
                    Order.created_at >= day,
                    Order.created_at < day + timedelta(days=1),
                ).scalar() or 0
                daily_orders[day.strftime("%m-%d")] = cnt

            # 各医院订单量排名
            hospital_order_count = {}
            hospitals = db.query(Hospital).all()
            for h in hospitals:
                cnt = db.query(func.count(Order.id)).filter(
                    Order.hospital_id == h.id
                ).scalar() or 0
                if cnt > 0:
                    hospital_order_count[h.name] = cnt

            # === 2. 用户分析 ===
            total_users = db.query(func.count(H5User.id)).scalar() or 0

            daily_new_users = {}
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                cnt = db.query(func.count(H5User.id)).filter(
                    H5User.created_at >= day,
                    H5User.created_at < day + timedelta(days=1),
                ).scalar() or 0
                daily_new_users[day.strftime("%m-%d")] = cnt

            # 有订单的用户数（活跃用户）
            active_users = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0

            # === 3. 陪诊师分析 ===
            companions = db.query(Companion).filter(Companion.active == 1).all()
            companion_stats = []
            for c in companions:
                order_cnt = db.query(func.count(Order.id)).filter(
                    Order.companion_id == c.id
                ).scalar() or 0
                companion_stats.append({
                    "name": c.name,
                    "total_orders": order_cnt,
                    "gender": "男" if c.sex == 1 else "女",
                })

            # === 4. AI客服分析 ===
            total_convs = db.query(func.count(AgentConversation.id)).scalar() or 0
            week_convs = db.query(func.count(AgentConversation.id)).filter(
                AgentConversation.created_at >= week_ago
            ).scalar() or 0

            negative_feedback = db.query(func.count(AgentFeedback.id)).filter(
                AgentFeedback.rating == 2
            ).scalar() or 0
            positive_feedback = db.query(func.count(AgentFeedback.id)).filter(
                AgentFeedback.rating == 1
            ).scalar() or 0

            total_feedback = negative_feedback + positive_feedback or 1
            satisfaction_rate = round(positive_feedback / total_feedback * 100, 1)

            return {
                "orders": {
                    "total": total,
                    "week_status": week_status,
                    "daily_trend": daily_orders,
                    "hospital_ranking": dict(sorted(
                        hospital_order_count.items(), key=lambda x: -x[1]
                    )[:5]),
                },
                "users": {
                    "total": total_users,
                    "daily_new": daily_new_users,
                    "active_users": active_users,
                },
                "companions": {
                    "total": len(companions),
                    "stats": companion_stats,
                },
                "ai_service": {
                    "total_conversations": total_convs,
                    "week_conversations": week_convs,
                    "satisfaction_rate": satisfaction_rate,
                    "negative_count": negative_feedback,
                },
                "date_range": f"{week_ago.strftime('%m-%d')} ~ {today.strftime('%m-%d')}",
            }
        finally:
            db.close()

    async def process(self, user_input: str = "", context: dict = None) -> dict:
        """深度分析业务数据"""
        analytics = self._collect_analytics()
        focus = (context or {}).get("focus", "all")

        analytics_text = json.dumps(analytics, ensure_ascii=False, indent=2)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "近7天业务数据如下，请进行分析（重点关注{focus}）：\n\n{analytics}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "focus": focus,
            "analytics": analytics_text,
        })

        dimensions = []
        key_findings = []
        action_items = []
        summary = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                dimensions = data.get("dimensions", [])
                key_findings = data.get("key_findings", [])
                action_items = data.get("action_items", [])
                summary = data.get("summary", "")
        except Exception:
            pass

        return {
            "reply": f"📈 业务分析报告\n\n{summary}",
            "meta_data": {
                "dimensions": dimensions,
                "key_findings": key_findings,
                "action_items": action_items,
                "summary": summary,
                "analytics": analytics,
            },
        }
