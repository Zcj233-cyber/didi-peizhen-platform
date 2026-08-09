"""运营分析 Agent - 数据统计与运营建议"""
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
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

    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理运营分析查询"""
        # 走 MCP 工具层收集运营统计数据
        raw = mcp.get_business_stats(include_week=True)
        stats = {
            "total_orders": raw["total_orders"],
            "today_orders": raw["today_orders"],
            "status_distribution": raw["status_distribution"],
            "total_users": raw["total_users"],
            "new_users_week": raw["week_users"],
            "total_companions": raw["active_companions"],
        }

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
