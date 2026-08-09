"""分诊推荐 Agent - 症状分析 + 医院科室推荐 + 陪诊师推荐"""
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent


class TriageAgent(BaseAgent):
    """分诊推荐 Agent：根据症状推荐科室、医院、陪诊师"""

    def __init__(self):
        super().__init__("triage")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个专业的医疗分诊助手。请根据用户的症状描述，推荐合适的就诊科室和医院。\n\n"
            "重要规则：\n"
            "1. 你只能推荐科室和医院，绝不下诊断或开药方\n"
            "2. 必须在推荐中注明推荐仅供参考\n"
            "3. 如果症状紧急（如胸痛、大出血等），必须提示紧急就医\n\n"
            "请以JSON格式输出结果，包含以下字段：\n"
            "- recommended_department: 推荐的科室名称\n"
            "- symptom_summary: 症状分析摘要\n"
            "- urgency_level: 紧急程度 normal/urgent/emergency\n"
            "- disclaimer: 免责声明"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """分析症状并推荐"""
        # 走 MCP 工具层取数
        hospitals = mcp.search_hospitals(limit=200)["hospitals"]
        companions = mcp.list_companions(active_only=True, limit=200)["companions"]
        hospital_list = "\n".join([
            f"- {h['name']}（{h['rank'] or '未评级'}）"
            for h in hospitals
        ])
        companion_list = "\n".join([
            f"- {c['name']}（{'女' if c['sex'] == 2 else '男'}，{c['age']}岁）"
            for c in companions
        ])

        age_info = ""
        if context and context.get("patient_age"):
            age_info = f"，年龄{context['patient_age']}岁"
        gender_info = ""
        if context and context.get("patient_gender"):
            gender_info = f"，性别{context['patient_gender']}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", (
                "用户症状描述：{symptoms}\n\n"
                "可推荐的医院：\n{hospitals}\n\n"
                "可推荐的陪诊师：\n{companions}\n\n"
                "请分析并返回JSON格式的推荐结果，只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "symptoms": f"{user_input}{age_info}{gender_info}",
            "hospitals": hospital_list,
            "companions": companion_list,
        })

        # 解析 JSON 结果
        recommended_department = "内科"
        urgency_level = "normal"
        symptom_summary = user_input
        disclaimer = "以上推荐仅供参考，请以医生诊断为准"

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                recommended_department = data.get("recommended_department", recommended_department)
                urgency_level = data.get("urgency_level", "normal")
                symptom_summary = data.get("symptom_summary", user_input)
                disclaimer = data.get("disclaimer", disclaimer)
        except Exception:
            pass

        # 获取天气与出行建议（走 MCP 工具层）
        weather_data = {"condition": "未知", "temperature": 20}
        travel_advice = ""
        try:
            weather_data = await mcp.get_weather()
            travel_advice = mcp.get_travel_advice(
                condition=weather_data["condition"],
                temperature=weather_data["temperature"],
                wind=weather_data.get("wind", ""),
            )["advice"]
        except Exception:
            pass

        return {
            "reply": f"根据您的描述，建议您前往 **{recommended_department}** 就诊。\n\n【出行提示】{travel_advice}",
            "meta_data": {
                "recommended_department": recommended_department,
                "recommended_hospitals": [
                    {"id": h["id"], "name": h["name"], "rank": h["rank"]}
                    for h in hospitals
                ],
                "recommended_companions": [
                    {"id": c["id"], "name": c["name"], "sex": "女" if c["sex"] == 2 else "男", "age": c["age"]}
                    for c in companions
                ],
                "symptom_summary": symptom_summary,
                "urgency_level": urgency_level,
                "disclaimer": disclaimer,
                "weather": weather_data,
                "travel_advice": travel_advice,
            },
        }
