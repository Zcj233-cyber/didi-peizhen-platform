"""智能报告 Agent - 生成运营日报/周报"""
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Order, H5User
from .base import BaseAgent


class ReportAgent(BaseAgent):
    """智能报告 Agent：自动生成运营报告"""

    def __init__(self):
        super().__init__("admin_report")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个医疗陪诊平台的运营报告编辑，将业务数据整理成结构清晰、可读性强的运营报告。\n\n"
            "报告结构：\n"
            "1. 📊 核心指标（今日 vs 昨日对比）\n"
            "2. 📦 订单动态（新增、完成、取消）\n"
            "3. 👥 用户动态\n"
            "4. ⚠️ 值得关注的问题\n"
            "5. 💡 运营建议\n\n"
            "要求：\n"
            "- 语言简洁有力，突出变化（上升/下降用百分比）\n"
            "- 好话坏话都说，不回避问题\n"
            "- 建议具体可执行\n\n"
            "请以JSON格式输出：\n"
            "- report_title: 报告标题\n"
            "- report_date: 报告日期\n"
            "- sections: 报告段落列表（每项含 icon, title, content）\n"
            "- highlights: 亮点列表\n"
            "- risks: 风险列表\n"
            "- suggestions: 改进建议\n"
            "- closing: 结语"
        )

    def _collect_report_data(self, days: int = 1) -> dict:
        """采集报告数据"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            period_start = today - timedelta(days=days)

            # 今日 vs 昨日
            today_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= today
            ).scalar() or 0
            yesterday_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= yesterday, Order.created_at < today
            ).scalar() or 0

            today_completed = db.query(func.count(Order.id)).filter(
                Order.created_at >= today, Order.trade_state == "已完成"
            ).scalar() or 0
            today_cancelled = db.query(func.count(Order.id)).filter(
                Order.created_at >= today, Order.trade_state == "已取消"
            ).scalar() or 0
            today_pending = db.query(func.count(Order.id)).filter(
                Order.created_at >= today, Order.trade_state == "待支付"
            ).scalar() or 0

            today_revenue = db.query(func.sum(Order.paid_price)).filter(
                Order.created_at >= today
            ).scalar() or 0
            yesterday_revenue = db.query(func.sum(Order.paid_price)).filter(
                Order.created_at >= yesterday, Order.created_at < today
            ).scalar() or 0

            today_users = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= today
            ).scalar() or 0
            yesterday_users = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= yesterday, H5User.created_at < today
            ).scalar() or 0

            # 周期汇总
            period_orders = db.query(func.count(Order.id)).filter(
                Order.created_at >= period_start
            ).scalar() or 0
            period_revenue = db.query(func.sum(Order.paid_price)).filter(
                Order.created_at >= period_start
            ).scalar() or 0

            # 订单状态总览
            all_status = {}
            for s in ["待支付", "待服务", "已完成", "已取消"]:
                all_status[s] = db.query(func.count(Order.id)).filter(
                    Order.trade_state == s
                ).scalar() or 0

            return {
                "date": today.strftime("%Y-%m-%d"),
                "period_days": days,
                "orders": {
                    "today_new": today_orders,
                    "yesterday_new": yesterday_orders,
                    "today_completed": today_completed,
                    "today_cancelled": today_cancelled,
                    "today_pending": today_pending,
                    "period_total": period_orders,
                    "all_status": all_status,
                },
                "revenue": {
                    "today": float(today_revenue),
                    "yesterday": float(yesterday_revenue),
                    "period": float(period_revenue),
                },
                "users": {
                    "today_new": today_users,
                    "yesterday_new": yesterday_users,
                },
            }
        finally:
            db.close()

    async def process(self, user_input: str = "", context: dict = None) -> dict:
        """生成运营报告"""
        days = (context or {}).get("days", 1)
        report_type = "日报" if days <= 1 else "周报"
        data = self._collect_report_data(days)

        data_text = json.dumps(data, ensure_ascii=False, indent=2)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "以下是{report_type}数据，请生成报告：\n\n{data}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "report_type": report_type,
            "data": data_text,
        })

        report_title = f"运营{report_type}"
        sections = []
        highlights = []
        risks = []
        suggestions = []
        closing = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                parsed = json.loads(json_str)
                report_title = parsed.get("report_title", report_title)
                sections = parsed.get("sections", [])
                highlights = parsed.get("highlights", [])
                risks = parsed.get("risks", [])
                suggestions = parsed.get("suggestions", [])
                closing = parsed.get("closing", "")
        except Exception:
            pass

        return {
            "reply": f"📋 **{report_title}** ({data['date']})\n\n" + "\n".join(
                [f"{s.get('icon','')} {s.get('title','')}\n{s.get('content','')}" for s in sections[:2]]
            ),
            "meta_data": {
                "report_title": report_title,
                "report_date": data["date"],
                "sections": sections,
                "highlights": highlights,
                "risks": risks,
                "suggestions": suggestions,
                "closing": closing,
                "data": data,
            },
        }
