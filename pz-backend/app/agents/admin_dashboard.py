"""Admin 智能运营中心 - 单Agent合并预警+分析+报告，大幅减少token消耗"""
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Order, H5User, Companion
from .base import BaseAgent


class AdminSuperAgent(BaseAgent):
    """超级运营Agent：一次LLM调用完成预警+分析+报告"""

    def __init__(self):
        super().__init__("admin_super")

    def _default_system_prompt(self) -> str:
        return (
            "你是医疗陪诊平台的运营AI。根据紧凑数据输出JSON。\n"
            "字段规范：\n"
            'alerts数组，每项含 level(danger/warning/info), dimension(维度), detail(详情), suggestion(建议).\n'
            'analysis对象含 key_findings(核心发现列表), dimensions(维度分析列表，每项含name标题,data数据,insight洞察,suggestion建议).\n'
            'report对象含 summary(总结), highlights(亮点列表), risks(风险列表), suggestions(改进建议列表).\n'
            "只返回纯JSON，不要多余文字。"
        )

    def _collect_compact_metrics(self) -> str:
        """采集最精简的业务指标，大幅减少token"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)

            # 今日/昨日/近7日汇总 - 一行搞定
            t_orders = db.query(func.count(Order.id)).scalar() or 0
            t_today = db.query(func.count(Order.id)).filter(Order.created_at >= today).scalar() or 0
            t_yest = db.query(func.count(Order.id)).filter(Order.created_at >= yesterday, Order.created_at < today).scalar() or 0
            t_week = db.query(func.count(Order.id)).filter(Order.created_at >= week_ago).scalar() or 0

            # 状态分布
            status = {}
            for s in ["待支付", "待服务", "已完成", "已取消"]:
                status[s] = db.query(func.count(Order.id)).filter(Order.trade_state == s).scalar() or 0

            # 用户
            u_total = db.query(func.count(H5User.id)).scalar() or 0
            u_today = db.query(func.count(H5User.id)).filter(H5User.created_at >= today).scalar() or 0
            u_yest = db.query(func.count(H5User.id)).filter(H5User.created_at >= yesterday, H5User.created_at < today).scalar() or 0

            # 陪诊师
            c_active = db.query(func.count(Companion.id)).filter(Companion.active == 1).scalar() or 0

            # 收入估算
            rev_today = float(db.query(func.sum(Order.paid_price)).filter(Order.created_at >= today).scalar() or 0)

            return (
                f"订单:总{t_orders},今{t_today},昨{t_yest},近7天{t_week},"
                f"待支付{status['待支付']},待服务{status['待服务']},已完成{status['已完成']},已取消{status['已取消']}|"
                f"用户:总{u_total},今{u_today},昨{u_yest}|"
                f"陪诊师:活跃{c_active}|"
                f"收入(元):今{rev_today}"
            )
        finally:
            db.close()

    async def process(self, user_input: str = "", context: dict = None) -> dict:
        """一次调用完成预警+分析+报告"""
        metrics = self._collect_compact_metrics()  # 仅~200字符，原来几千字符

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "业务数据：{metrics}\n\n分析异常并给出运营建议。"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"metrics": metrics})

        alerts = []
        analysis = {"key_findings": [], "dimensions": []}
        report = {"summary": "", "highlights": [], "risks": [], "suggestions": []}

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                alerts = data.get("alerts", [])
                analysis = data.get("analysis", analysis)
                report = data.get("report", report)
        except Exception:
            pass

        return {
            "alerts": alerts,
            "has_alert": len(alerts) > 0,
            "analysis": analysis,
            "report": report,
            # 紧凑指标供前端展示
            "metrics_flat": metrics,
        }


# 保持接口兼容
class AdminOrchestrator:
    """兼容旧接口，实际委托给AdminSuperAgent一次调用完成"""

    def __init__(self):
        self._agent = AdminSuperAgent()

    async def dashboard(self) -> dict:
        result = await self._agent.process()
        alerts = result.get("alerts", [])
        analysis_raw = result.get("analysis", {})
        report_raw = result.get("report", {})

        # analysis可能是dict或list，兼容两种格式
        if isinstance(analysis_raw, dict):
            key_findings = analysis_raw.get("key_findings", [])
            dimensions = analysis_raw.get("dimensions", [])
        elif isinstance(analysis_raw, list):
            key_findings = analysis_raw
            dimensions = []
        else:
            key_findings = []
            dimensions = []

        # report兼容
        if isinstance(report_raw, dict):
            highlights = report_raw.get("highlights", [])
            risks = report_raw.get("risks", [])
            suggestions = report_raw.get("suggestions", [])
            summary = report_raw.get("summary", "")
        else:
            highlights = []
            risks = []
            suggestions = []
            summary = str(report_raw) if report_raw else ""

        return {
            "alerts": alerts,
            "has_alert": result.get("has_alert", len(alerts) > 0),
            "analysis": analysis_raw,
            "report": report_raw,
            "alert_metrics": {},
            "analytics": {
                "key_findings": key_findings,
                "dimensions": dimensions,
                "action_items": suggestions,
                "analytics": {},
            },
            "report": {
                "report_title": "运营日报",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "sections": [],
                "highlights": highlights,
                "risks": risks,
                "suggestions": suggestions,
                "closing": summary,
            },
        }

    async def alert_only(self) -> dict:
        result = await self._agent.process()
        return {"alerts": result["alerts"], "has_alert": result["has_alert"]}

    async def analytics_only(self, focus: str = "all") -> dict:
        result = await self._agent.process()
        analysis_raw = result.get("analysis", {})
        report_raw = result.get("report", {})
        if isinstance(analysis_raw, dict):
            findings = analysis_raw.get("key_findings", [])
            dims = analysis_raw.get("dimensions", [])
        elif isinstance(analysis_raw, list):
            findings = analysis_raw
            dims = []
        else:
            findings = []
            dims = []
        suggestions = report_raw.get("suggestions", []) if isinstance(report_raw, dict) else []
        return {
            "key_findings": findings,
            "dimensions": dims,
            "action_items": suggestions,
            "analytics": {},
        }

    async def report_only(self, days: int = 1) -> dict:
        result = await self._agent.process()
        r = result.get("report", {})
        if isinstance(r, dict):
            highlights = r.get("highlights", [])
            risks = r.get("risks", [])
            suggestions = r.get("suggestions", [])
            summary = r.get("summary", "")
        else:
            highlights = []
            risks = []
            suggestions = []
            summary = str(r) if r else ""
        return {
            "reply": summary,
            "report_title": "运营日报" if days <= 1 else "运营周报",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "sections": [],
            "highlights": highlights,
            "risks": risks,
            "suggestions": suggestions,
            "closing": summary,
        }
