"""智能预警 Agent - 主动检测业务异常"""
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Order, H5User, Companion
from app.agent_models import AgentFeedback
from .base import BaseAgent


class AlertAgent(BaseAgent):
    """智能预警 Agent：主动检测业务异常和风险"""

    def __init__(self):
        super().__init__("admin_alert")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个医疗陪诊平台的智能预警分析师。根据实时业务数据，检测异常和风险。\n\n"
            "关注以下维度：\n"
            "1. 订单异常：今日订单量较昨日/上周同期异常下降\n"
            "2. 取消率：取消订单占比是否偏高\n"
            "3. 待支付积压：长期未支付订单堆积\n"
            "4. 陪诊师负载：是否有陪诊师工作量过高或过低\n"
            "5. 用户增长：新注册用户数是否异常\n\n"
            "请以JSON格式输出，包含：\n"
            "- alerts: 预警列表（每项含 level: warning/danger/info, dimension, detail, suggestion）\n"
            "- has_alert: 是否有预警\n"
            "- summary: 一句话总结"
        )

    def _collect_metrics(self) -> dict:
        """采集各项业务指标"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            last_week_start = today - timedelta(days=14)
            last_week_end = today - timedelta(days=7)

            # === 订单指标 ===
            total_orders = db.query(func.count(Order.id)).scalar() or 0

            # 今日订单
            today_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= today
            ).scalar() or 0

            # 昨日订单
            yesterday_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= yesterday, Order.created_at < today
            ).scalar() or 0

            # 本周订单（近7天）
            week_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= week_ago
            ).scalar() or 0

            # 上周同期订单
            last_week_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= last_week_start,
                Order.created_at < last_week_end
            ).scalar() or 0

            # 各状态订单数
            status_dist = {}
            for s in ["待支付", "待服务", "已完成", "已取消"]:
                status_dist[s] = db.query(func.count(Order.id)).filter(
                    Order.trade_state == s
                ).scalar() or 0

            # 取消率
            total_valid = total_orders or 1
            cancel_rate = round(status_dist.get("已取消", 0) / total_valid * 100, 1)

            # 待支付超过30分钟的订单
            thirty_min_ago = int((now - timedelta(minutes=30)).timestamp() * 1000)
            long_unpaid = db.query(func.count(Order.id)).filter(
                Order.trade_state == "待支付",
                Order.order_start_time < thirty_min_ago,
                Order.order_start_time > 0,
            ).scalar() or 0

            # === 用户指标 ===
            total_users = db.query(func.count(H5User.id)).scalar() or 0
            new_users_today = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= today
            ).scalar() or 0
            new_users_yesterday = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= yesterday,
                H5User.created_at < today
            ).scalar() or 0

            # === 陪诊师指标 ===
            total_companions = db.query(func.count(Companion.id)).filter(
                Companion.active == 1
            ).scalar() or 0

            # 每个陪诊师近7天服务订单数
            companion_workload = {}
            companions = db.query(Companion).filter(Companion.active == 1).all()
            for c in companions:
                order_count = db.query(func.count(Order.id)).filter(
                    Order.companion_id == c.id,
                    Order.created_at >= week_ago,
                    Order.trade_state.in_(["待服务", "已完成"]),
                ).scalar() or 0
                companion_workload[c.name] = order_count

            # === 用户反馈 ===
            recent_feedback = db.query(func.count(AgentFeedback.id)).filter(
                AgentFeedback.created_at >= week_ago,
                AgentFeedback.rating == 2,  # 差评
            ).scalar() or 0

            return {
                "total_orders": total_orders,
                "today_orders": today_orders,
                "yesterday_orders": yesterday_orders,
                "week_orders": week_orders,
                "last_week_orders": last_week_orders,
                "status_distribution": status_dist,
                "cancel_rate": cancel_rate,
                "long_unpaid": long_unpaid,
                "total_users": total_users,
                "new_users_today": new_users_today,
                "new_users_yesterday": new_users_yesterday,
                "total_companions": total_companions,
                "companion_workload": companion_workload,
                "recent_feedback_negative": recent_feedback,
                "date": now.strftime("%Y-%m-%d"),
            }
        finally:
            db.close()

    async def process(self, user_input: str = "", context: dict = None) -> dict:
        """检测业务异常"""
        metrics = self._collect_metrics()

        metrics_text = json.dumps(metrics, ensure_ascii=False, indent=2)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "以下是今天的业务数据，请分析异常情况：\n\n{metrics}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"metrics": metrics_text})

        alerts = []
        has_alert = False
        summary = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                alerts = data.get("alerts", [])
                has_alert = data.get("has_alert", len(alerts) > 0)
                summary = data.get("summary", "")
        except Exception:
            pass

        # 补充硬性规则预警（不依赖LLM）
        hard_alerts = []
        if metrics["today_orders"] == 0 and metrics["yesterday_orders"] > 0:
            hard_alerts.append({
                "level": "danger",
                "dimension": "订单量",
                "detail": f"今日至今仍无新订单，而昨日有{metrics['yesterday_orders']}单",
                "suggestion": "检查前端是否正常、是否有线上异常",
            })
        if metrics["long_unpaid"] >= 3:
            hard_alerts.append({
                "level": "warning",
                "dimension": "支付积压",
                "detail": f"有{metrics['long_unpaid']}个订单待支付超过30分钟",
                "suggestion": "可发送支付提醒或联系用户确认",
            })
        if metrics["cancel_rate"] > 30:
            hard_alerts.append({
                "level": "warning",
                "dimension": "取消率",
                "detail": f"订单取消率达{metrics['cancel_rate']}%，高于正常水平",
                "suggestion": "检查近期订单取消原因，是否存在服务质量问题",
            })

        all_alerts = hard_alerts + alerts

        return {
            "reply": f"📊 今日业务预警：{'有' if all_alerts else '无'}异常\n\n{summary}",
            "meta_data": {
                "alerts": all_alerts,
                "has_alert": len(all_alerts) > 0,
                "summary": summary,
                "metrics": metrics,
            },
        }
