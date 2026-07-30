"""分诊推荐 Agent - 症状分析 + 医院科室推荐 + 陪诊师推荐"""
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import SessionLocal
from app.models import Hospital
from app.utils.weather import fetch_weather, get_travel_advice
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
        db = SessionLocal()
        try:
            hospitals = db.query(Hospital).all()
            # 精简：只传医院名和等级，去掉label/intro，去掉陪诊师列表
            hospital_list = "\n".join([
                f"- {h.name}（{h.rank or '未评级'}）"
                for h in hospitals
            ])
        finally:
            db.close()

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
                "请分析并返回JSON格式的推荐结果，只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "symptoms": f"{user_input}{age_info}{gender_info}",
            "hospitals": hospital_list,
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

        # 获取天气与出行建议
        weather_data = {"condition": "未知", "temperature": 20}
        travel_advice = ""
        try:
            import asyncio
            weather_data = await fetch_weather()
            travel_advice = get_travel_advice(weather_data)
        except Exception:
            pass

        return {
            "reply": f"根据您的描述，建议您前往 **{recommended_department}** 就诊。\n\n【出行提示】{travel_advice}",
            "meta_data": {
                "recommended_department": recommended_department,
                "recommended_hospitals": [
                    {"id": h.id, "name": h.name, "rank": h.rank}
                    for h in hospitals
                ],
                "recommended_companions": [],
                "symptom_summary": symptom_summary,
                "urgency_level": urgency_level,
                "disclaimer": disclaimer,
                "weather": weather_data,
                "travel_advice": travel_advice,
            },
        }
