"""费用预估 Agent - 根据科室、城市、医院等级预估就诊费用"""
import asyncio
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent
from .results import parse_result


class CostEstimatorAgent(BaseAgent):
    """费用预估 Agent：预估挂号费、检查费，提供医保参考"""

    def __init__(self):
        super().__init__("cost_estimator")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个医疗费用预估顾问。根据就诊科室、城市和医院等级，预估看病费用。\n\n"
            "重要规则：\n"
            "1. 分项列出费用组成（挂号费、检查费、药费等）\n"
            "2. 给出价格区间（低-高），说明影响因素\n"
            "3. 提供医保报销的大致参考比例\n"
            "4. 如果用户选择了陪诊服务，告知陪诊费用\n"
            "5. 所有价格均为预估，需注明实际以医院为准\n\n"
            "请以JSON格式输出，包含以下字段：\n"
            "- registration_fee: 挂号费区间（字符串，如'20-100元'）\n"
            "- exam_fee: 检查费预估区间（如'200-800元'）\n"
            "- medicine_fee: 药费预估\n"
            "- total_range: 总费用区间\n"
            "- insurance_ratio: 医保报销比例参考\n"
            "- companion_fee: 陪诊服务费用（如果平台有价格）\n"
            "- breakdown: 费用明细列表（每项含 name, range, note）\n"
            "- disclaimer: 费用说明"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """预估费用"""
        department = (context or {}).get("department", "内科")
        city = (context or {}).get("city", "武汉")
        hospital_name = (context or {}).get("hospital_name", "")
        hospital_rank = (context or {}).get("hospital_rank", "")
        if not hospital_name or not hospital_rank:
            raise ValueError("verified hospital basis required")

        # 查陪诊服务价格（走 MCP 工具层）
        services = (await asyncio.to_thread(mcp.list_services, limit=1))["services"]
        service = services[0] if services else None
        companion_price = service["price"] if service else None
        service_name = service["name"] if service else "陪诊服务"

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", (
                "就诊信息：\n"
                "- 推荐科室：{department}\n"
                "- 所在城市：{city}\n"
                "- 推荐医院：{hospital_name}\n"
                "- 医院等级：{hospital_rank}\n"
                "- 平台陪诊价：{companion_price}元/次（{service_name}）\n\n"
                "请根据以上信息进行费用预估。只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "department": department,
            "city": city,
            "hospital_name": hospital_name,
            "hospital_rank": hospital_rank,
            "companion_price": companion_price if companion_price is not None else "暂无平台报价",
            "service_name": service_name,
        })

        # 解析结果
        data = parse_result(result, string_fields=("registration_fee", "exam_fee", "medicine_fee", "total_range", "insurance_ratio"),
                            list_fields=("breakdown",), required_text=("total_range",))
        registration_fee = data.get("registration_fee", "")
        exam_fee = data.get("exam_fee", "")
        medicine_fee = data.get("medicine_fee", "")
        total_range = data["total_range"]
        insurance_ratio = data.get("insurance_ratio", "")
        # 平台服务费取数据库报价，不允许模型改写成另一个价格。
        companion_fee = f"{companion_price:g}元" if companion_price is not None else ""
        breakdown = data.get("breakdown", [])
        if any(not isinstance(item, dict) or any(not isinstance(item.get(k, ""), str) for k in ("name", "range", "note")) for item in breakdown):
            raise ValueError("invalid cost breakdown")
        disclaimer = "以上医疗费用为模型参考估算，未接入医院实时收费表；实际收费与医保待遇以医院及当地政策为准。"

        return {
            "reply": f"预估前往 **{department}**（{hospital_rank}）就诊费用约为 **{total_range}**（医保报销约{insurance_ratio}）。",
            "meta_data": {
                "registration_fee": registration_fee,
                "exam_fee": exam_fee,
                "medicine_fee": medicine_fee,
                "total_range": total_range,
                "insurance_ratio": insurance_ratio,
                "companion_fee": companion_fee,
                "companion_price": companion_price,
                "service_name": service_name,
                "breakdown": breakdown,
                "disclaimer": disclaimer,
                "hospital_name": hospital_name,
                "hospital_rank": hospital_rank,
                "city": city,
            },
        }
