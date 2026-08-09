"""智能客服 Agent - FAQ匹配 + LLM增强"""
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent


class CustomerServiceAgent(BaseAgent):
    """智能客服 Agent：FAQ匹配 + LLM增强"""

    # FAQ相似度阈值
    FAQ_SIMILARITY_THRESHOLD = 0.42

    def __init__(self):
        super().__init__("customer_service")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个专业的医疗陪诊平台客服助手。你的职责是：\n"
            "1. 回答用户关于陪诊服务流程的问题\n"
            "2. 介绍服务项目和价格\n"
            "3. 解答预约、支付、取消等常见问题\n"
            "4. 保持友好、耐心、专业的语气，使用合适的表情符号\n"
            "5. 如果用户情绪不好，先表达理解和共情\n"
            "6. 回答要简洁有条理，重要信息可以分段\n"
            "7. 如果遇到不清楚的问题，诚实地告诉用户并提供联系方式"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理客服咨询 - FAQ优先，LLM补充"""
        # 1. 尝试FAQ匹配（走 MCP 工具层）
        faq_results = mcp.search_faq(query=user_input, top_k=5)["results"]
        faq_match = (
            faq_results[0]
            if faq_results and faq_results[0]["score"] >= self.FAQ_SIMILARITY_THRESHOLD
            else None
        )

        # 2. 收集业务数据做 grounding
        services = mcp.list_services()["services"]
        hospitals = mcp.search_hospitals(limit=5)["hospitals"]
        user_id = (context or {}).get("user_id", 0)

        service_info = "\n".join([
            f"- {s['name']}：¥{s['price']}/次"
            for s in services
        ]) if services else "暂无服务信息"

        hospital_info = "\n".join([
            f"- {h['name']}（{h['rank'] or '未评级'}）"
            for h in hospitals[:5]
        ])

        # 用户订单摘要（仅用于上下文）
        order_summary = ""
        if user_id:
            orders = mcp.get_user_orders(user_id=user_id, limit=3)["orders"]
            if orders:
                order_summary = "\n".join([
                    f"- {o['out_trade_no']}：{o['hospital_name']}，{o['trade_state']}"
                    for o in orders
                ])

        # 如果有FAQ匹配且置信度高，直接返回
        if faq_match and faq_match.get("score", 0) >= 0.7:
            return {
                "reply": faq_match["answer"],
                "meta_data": {
                    "agent_type": "customer_service",
                    "faq_matched": True,
                    "faq_question": faq_match["question"],
                    "faq_category": faq_match["category"],
                },
            }

        # 否则用LLM，注入FAQ+业务数据
        extra_context_parts = []
        if faq_match:
            extra_context_parts.append(
                f"【参考FAQ】\n问题：{faq_match['question']}\n答案：{faq_match['answer']}"
            )

        grounding = (
            f"【当前平台服务】\n{service_info}\n\n"
            f"【合作医院】\n{hospital_info}\n\n"
            f"{extra_context_parts[0] if extra_context_parts else ''}\n\n"
            f"【用户订单摘要】\n{order_summary if order_summary else '暂无'}\n"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "{grounding}\n\n用户问题：{input}\n\n请结合以上信息回答用户的问题。如果参考FAQ能回答就用FAQ的内容，不够的再补充。"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        reply = await chain.ainvoke({
            "grounding": grounding,
            "input": user_input,
        })

        return {
            "reply": reply,
            "meta_data": {
                "agent_type": "customer_service",
                "faq_matched": faq_match is not None,
                "faq_category": faq_match["category"] if faq_match else None,
            },
        }
