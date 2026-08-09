"""订单助手 Agent - 订单查询、改约、取消等"""
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent


class OrderAssistantAgent(BaseAgent):
    """订单助手 Agent：处理与订单相关的用户请求"""

    def __init__(self):
        super().__init__("order_assistant")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个订单助手，负责处理用户的订单相关问题。包括：\n"
            "1. 查询订单状态\n"
            "2. 处理改约请求\n"
            "3. 处理取消订单\n"
            "4. 发送催单提醒\n\n"
            "注意：只能查询当前登录用户的订单信息。保持友好专业的语气。"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理订单相关请求"""
        user_id = (context or {}).get("user_id", 0)
        orders = []
        if user_id:
            orders = mcp.get_user_orders(user_id=user_id, limit=5)["orders"]

        order_summary = "您暂无订单。" if not orders else "\n".join([
            f"- 订单号：{o['out_trade_no']}，状态：{o['trade_state']}，"
            f"医院：{o['hospital_name']}，时间：{o['starttime'] or '待定'}"
            for o in orders
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "{input}\n\n当前用户订单信息：\n{order_summary}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        reply = await chain.ainvoke({
            "input": user_input,
            "order_summary": order_summary,
        })

        return {
            "reply": reply,
            "meta_data": {
                "agent_type": "order_assistant",
                "order_count": len(orders),
            },
        }
