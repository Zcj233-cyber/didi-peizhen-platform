"""医院推荐 Agent - 根据科室和城市推荐最适合的医院与专家"""
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.mcp import client as mcp
from .base import BaseAgent


class HospitalAdvisorAgent(BaseAgent):
    """医院推荐 Agent：基于科室、城市、紧急程度推荐医院"""

    def __init__(self):
        super().__init__("hospital_advisor")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个专业的医院推荐顾问。根据用户的科室需求和所在城市，推荐最合适的医院。\n\n"
            "重要规则：\n"
            "1. 基于医院等级（三甲>三乙>二甲>二乙）、特色标签等信息排序\n"
            "2. 对每家医院给出简短推荐理由\n"
            "3. 如果有多家医院，列出2-3家供选择\n"
            "4. 必须注明推荐仅供参考\n\n"
            "请以JSON格式输出，包含以下字段：\n"
            "- recommended_hospitals: 推荐医院列表（每个含 name, rank, reason）\n"
            "- best_choice: 最佳推荐（医院名称）\n"
            "- summary: 推荐总结"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """根据科室和城市推荐医院"""
        department = (context or {}).get("department", "")
        city = (context or {}).get("city", "武汉")
        urgency = (context or {}).get("urgency_level", "normal")

        # 1. 查询该城市所有医院（走 MCP 工具层）
        hospitals = mcp.search_hospitals(city=city, limit=100)["hospitals"]

        # 2. 如果该城市没医院，扩大到周边或全国
        if not hospitals:
            hospitals = mcp.search_hospitals(limit=10)["hospitals"]
            city = "全国"

        # 3. 构建医院数据（精简：只留名称和等级，限前5家）
        hospital_list = "\n".join([
            f"- {h['name']}（{h['rank'] or '未评级'}）"
            for h in hospitals[:5]
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", (
                "用户需求：\n"
                "- 推荐科室：{department}\n"
                "- 所在城市：{city}\n"
                "- 紧急程度：{urgency}\n\n"
                "该城市可推荐的医院：\n{hospitals}\n\n"
                "请根据科室特点和医院等级，推荐最适合的医院并给出理由。"
                "只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "department": department,
            "city": city,
            "urgency": urgency,
            "hospitals": hospital_list,
        })

        # 解析结果
        recommended = []
        best_choice = ""
        summary = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                recommended = data.get("recommended_hospitals", [])
                best_choice = data.get("best_choice", "")
                summary = data.get("summary", "")
        except Exception:
            pass

        # 构建返回的医院数据（带完整信息）
        hospital_details = []
        seen_names = set()
        for h in hospitals:
            if h["name"] not in seen_names:
                seen_names.add(h["name"])
                hospital_details.append({
                    "id": h["id"],
                    "name": h["name"],
                    "rank": h["rank"] or "",
                    "label": h["label"] or "",
                    "intro": h["intro"][:100] if h["intro"] else "",
                    "address": h["address"] or "",
                    "latitude": h["latitude"] or "",
                    "longitude": h["longitude"] or "",
                    "avatar_url": h["avatar_url"] or "",
                })

        return {
            "reply": f"为您推荐了 **{city}** 的以下医院：\n\n{summary}",
            "meta_data": {
                "recommended_hospitals": recommended,
                "hospital_details": hospital_details,
                "best_choice": best_choice,
                "city": city,
            },
        }
