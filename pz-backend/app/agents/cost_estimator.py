"""费用预估 Agent - 根据科室、城市、医院等级预估就诊费用"""
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent


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
        hospital_rank = (context or {}).get("hospital_rank", "三甲")

        # 查陪诊服务价格（走 MCP 工具层）
        services = mcp.list_services(limit=1)["services"]
        service = services[0] if services else None
        companion_price = service["price"] if service else 0.5
        service_name = service["name"] if service else "陪诊服务"

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", (
                "就诊信息：\n"
                "- 推荐科室：{department}\n"
                "- 所在城市：{city}\n"
                "- 医院等级：{hospital_rank}\n"
                "- 平台陪诊价：{companion_price}元/次（{service_name}）\n\n"
                "请根据以上信息进行费用预估。只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "department": department,
            "city": city,
            "hospital_rank": hospital_rank,
            "companion_price": companion_price,
            "service_name": service_name,
        })

        # 解析结果
        registration_fee = ""
        exam_fee = ""
        medicine_fee = ""
        total_range = ""
        insurance_ratio = ""
        companion_fee = ""
        breakdown = []
        disclaimer = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                registration_fee = data.get("registration_fee", "20-100元")
                exam_fee = data.get("exam_fee", "200-500元")
                medicine_fee = data.get("medicine_fee", "100-300元")
                total_range = data.get("total_range", "300-1000元")
                insurance_ratio = data.get("insurance_ratio", "约50%-80%")
                companion_fee = data.get("companion_fee", f"{companion_price}元")
                breakdown = data.get("breakdown", [])
                disclaimer = data.get("disclaimer", "以上为预估费用，实际以医院收费为准")
        except Exception:
            pass

        return {
            "reply": f"预估前往 **{department}**（{hospital_rank}）就诊费用约为 **{total_range}**（医保报销约{insurance_ratio}）。",
            "meta_data": {
                "registration_fee": registration_fee,
                "exam_fee": exam_fee,
                "medicine_fee": medicine_fee,
                "total_range": total_range,
                "insurance_ratio": insurance_ratio,
                "companion_fee": companion_fee if companion_fee else f"{companion_price}元",
                "companion_price": companion_price,
                "service_name": service_name,
                "breakdown": breakdown,
                "disclaimer": disclaimer,
            },
        }
