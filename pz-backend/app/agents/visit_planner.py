"""就医规划 Orchestrator - 多Agent协作生成完整就诊攻略"""
import asyncio
import json
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.mcp import client as mcp

from .base import BaseAgent
from .triage_agent import TriageAgent
from .hospital_advisor import HospitalAdvisorAgent
from .prep_guide import PrepGuideAgent
from .cost_estimator import CostEstimatorAgent


class SynthesisAgent(BaseAgent):
    """综合Agent：将多Agent结果合并成一份完整的就诊攻略"""

    def __init__(self):
        super().__init__("synthesis")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个贴心的就医规划管家。你的任务是将多份信息合并成一份完整的、"
            "条理清晰的「就医攻略」，让患者一目了然。\n\n"
            "要求：\n"
            "1. 语气温暖亲切，让患者感到安心\n"
            "2. 按顺序组织：分诊建议→推荐医院→准备清单→费用预估→出行天气\n"
            "3. 突出最重要的信息（如空腹要求、紧急程度等）\n"
            "4. 最后给出总结建议\n"
            "5. 文案适合在手机端阅读，段落简短，善用emoji\n\n"
            "以JSON格式输出：\n"
            "- title: 攻略标题\n"
            "- summary: 一句话总结\n"
            "- guide_sections: 攻略分段内容列表（每项含 icon, title, content）\n"
            "- closing_tip: 结尾温馨提示"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """生成综合攻略"""
        triage = (context or {}).get("triage", {})
        hospitals = (context or {}).get("hospitals", {})
        prep = (context or {}).get("prep", {})
        cost = (context or {}).get("cost", {})
        weather_data = (context or {}).get("weather", {})
        travel_advice = (context or {}).get("travel_advice", "")
        patient_age = (context or {}).get("patient_age", "")
        patient_gender = (context or {}).get("patient_gender", "")

        triage_meta = triage.get("meta_data", {}) if isinstance(triage, dict) else {}
        prep_meta = prep.get("meta_data", {}) if isinstance(prep, dict) else {}
        cost_meta = cost.get("meta_data", {}) if isinstance(cost, dict) else {}
        hospital_meta = hospitals.get("meta_data", {}) if isinstance(hospitals, dict) else {}

        context_text = json.dumps({
            "症状分析": triage_meta.get("symptom_summary", ""),
            "推荐科室": triage_meta.get("recommended_department", ""),
            "紧急程度": triage_meta.get("urgency_level", "normal"),
            "推荐医院": hospital_meta.get("recommended_hospitals", []),
            "最佳推荐": hospital_meta.get("best_choice", ""),
            "准备清单": prep_meta.get("checklist", ""),
            "需带证件": prep_meta.get("documents", []),
            "饮食建议": prep_meta.get("diet_before", ""),
            "着装建议": prep_meta.get("clothing", ""),
            "特别提醒": prep_meta.get("special_notes", []),
            "费用预估": {
                "挂号费": cost_meta.get("registration_fee", ""),
                "检查费": cost_meta.get("exam_fee", ""),
                "总费用": cost_meta.get("total_range", ""),
                "医保报销": cost_meta.get("insurance_ratio", ""),
            },
            "天气": f"{weather_data.get('condition','')} {weather_data.get('temperature','')}°C",
            "出行建议": travel_advice,
            "患者年龄": patient_age,
            "患者性别": patient_gender,
        }, ensure_ascii=False)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "以下是所有信息，请整合成一份完整的就医攻略：\n\n{context}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"context": context_text})

        title = "就诊攻略"
        summary = ""
        guide_sections = []
        closing_tip = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                title = data.get("title", "就诊攻略")
                summary = data.get("summary", "")
                guide_sections = data.get("guide_sections", [])
                closing_tip = data.get("closing_tip", "")
        except Exception:
            pass

        return {
            "reply": f"📋 **{title}**\n\n{summary}",
            "meta_data": {
                "title": title,
                "summary": summary,
                "guide_sections": guide_sections,
                "closing_tip": closing_tip,
            },
        }


class VisitPlannerOrchestrator:
    """就医规划编排器 - 多Agent协作"""

    def __init__(self):
        self.triage_agent = TriageAgent()
        self.hospital_advisor = HospitalAdvisorAgent()
        self.prep_guide = PrepGuideAgent()
        self.cost_estimator = CostEstimatorAgent()
        self.synthesis_agent = SynthesisAgent()

    def _find_nearest_city(self, lat: float, lng: float) -> str:
        """根据坐标找到最近的城市"""
        CITY_COORDS = {
            "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
            "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
            "武汉": (30.5928, 114.3055), "成都": (30.5728, 104.0668),
            "杭州": (30.2741, 120.1551), "南京": (32.0603, 118.7969),
            "重庆": (29.4316, 106.9123), "西安": (34.3416, 108.9398),
            "长沙": (28.2282, 112.9388), "郑州": (34.7466, 113.6254),
        }
        nearest = "武汉"
        min_dist = float("inf")
        for city, (clat, clng) in CITY_COORDS.items():
            dist = mcp.calc_distance(lat, lng, clat, clng)["distance_km"]
            if dist < min_dist:
                min_dist = dist
                nearest = city
        return nearest

    async def plan(
        self,
        symptoms: str,
        patient_age: int = 0,
        patient_gender: str = "",
        city: str = "",
        lat: float = None,
        lng: float = None,
        user_id: int = 0,
    ) -> dict:
        """
        多Agent协作生成完整就医攻略

        Phase 1: 分诊分析（顺序执行）
        Phase 2: 并行查询（医院、准备、费用、天气）
        Phase 3: 综合生成攻略
        """
        # 确定城市
        if not city and lat is not None and lng is not None:
            city = self._find_nearest_city(lat, lng)
        if not city:
            city = "武汉"

        # ==================== Phase 1: 分诊 ====================
        triage_context = {"patient_age": patient_age, "patient_gender": patient_gender}
        triage_result = await self.triage_agent.process(symptoms, triage_context)
        triage_meta = triage_result.get("meta_data", {})
        department = triage_meta.get("recommended_department", "内科")
        urgency = triage_meta.get("urgency_level", "normal")

        # 获取医院的等级用于费用预估（走 MCP 工具层）
        hospitals = mcp.search_hospitals(city=city, limit=1)["hospitals"]
        hospital_rank = hospitals[0]["rank"] if hospitals else "三甲"

        # ==================== Phase 2: 并行执行 ====================
        # 所有Agent共享的上下文
        shared_context = {
            "department": department,
            "city": city,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "urgency_level": urgency,
            "hospital_rank": hospital_rank,
        }

        hospital_task = self.hospital_advisor.process(
            f"推荐{department}的医院", shared_context
        )
        prep_task = self.prep_guide.process(
            f"准备去{department}就诊", shared_context
        )
        cost_task = self.cost_estimator.process(
            f"预估{department}就诊费用", shared_context
        )

        # 天气和出行建议（不调LLM，用 MCP 工具）
        async def get_weather_and_advice():
            try:
                weather_data = await mcp.get_weather(city)
                advice = mcp.get_travel_advice(
                    condition=weather_data["condition"],
                    temperature=weather_data["temperature"],
                    wind=weather_data.get("wind", ""),
                    dest_name="医院",
                )["advice"]
                return weather_data, advice
            except Exception:
                return {"condition": "未知", "temperature": 20}, "天气信息获取失败"

        weather_task = get_weather_and_advice()

        # 并发执行所有任务
        hospital_result, prep_result, cost_result, (weather_data, travel_advice) = (
            await asyncio.gather(
                hospital_task, prep_task, cost_task, weather_task
            )
        )

        # 提取各Agent的meta_data
        prep_meta = prep_result.get("meta_data", {}) if isinstance(prep_result, dict) else {}
        cost_meta = cost_result.get("meta_data", {}) if isinstance(cost_result, dict) else {}
        hospital_meta = hospital_result.get("meta_data", {}) if isinstance(hospital_result, dict) else {}

        # ==================== Phase 3: 综合 ====================
        synthesis_result = await self.synthesis_agent.process(symptoms, {
            "triage": triage_result,
            "hospitals": hospital_result,
            "prep": prep_result,
            "cost": cost_result,
            "weather": weather_data,
            "travel_advice": travel_advice,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
        })
        synthesis_meta = synthesis_result.get("meta_data", {})

        # ==================== 组装最终结果 ====================
        return {
            "guide_title": synthesis_meta.get("title", "就诊攻略"),
            "guide_summary": synthesis_meta.get("summary", ""),
            "guide_sections": synthesis_meta.get("guide_sections", []),
            "closing_tip": synthesis_meta.get("closing_tip", ""),
            "guide_reply": synthesis_result.get("reply", ""),
            # 各Agent原始数据（前端展示用）
            "triage": {
                "recommended_department": department,
                "symptom_summary": triage_meta.get("symptom_summary", symptoms),
                "urgency_level": urgency,
                "disclaimer": triage_meta.get("disclaimer", ""),
            },
            "hospitals": {
                "list": hospital_meta.get("hospital_details", []),
                "recommended": hospital_meta.get("recommended_hospitals", []),
                "best_choice": hospital_meta.get("best_choice", ""),
                "city": city,
            },
            "prep_guide": {
                "documents": prep_meta.get("documents", []),
                "diet_before": prep_meta.get("diet_before", ""),
                "clothing": prep_meta.get("clothing", ""),
                "special_notes": prep_meta.get("special_notes", []),
                "checklist": prep_meta.get("checklist", ""),
            },
            "cost_estimate": {
                "registration_fee": cost_meta.get("registration_fee", ""),
                "exam_fee": cost_meta.get("exam_fee", ""),
                "medicine_fee": cost_meta.get("medicine_fee", ""),
                "total_range": cost_meta.get("total_range", ""),
                "insurance_ratio": cost_meta.get("insurance_ratio", ""),
                "companion_fee": cost_meta.get("companion_fee", ""),
                "breakdown": cost_meta.get("breakdown", []),
                "disclaimer": cost_meta.get("disclaimer", ""),
            },
            "weather": {
                "condition": weather_data.get("condition", ""),
                "temperature": weather_data.get("temperature", ""),
                "wind": weather_data.get("wind", ""),
                "humidity": weather_data.get("humidity", ""),
            },
            "travel_advice": travel_advice,
        }
