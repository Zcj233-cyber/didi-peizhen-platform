"""就诊准备指南 Agent - 根据科室和患者情况提供就医准备清单"""
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .base import BaseAgent


class PrepGuideAgent(BaseAgent):
    """就诊准备指南 Agent：生成就医前准备清单"""

    def __init__(self):
        super().__init__("prep_guide")

    def _default_system_prompt(self) -> str:
        return (
            "你是一个贴心的就医准备顾问。根据患者的就诊科室和情况，生成详细的就医前准备清单。\n\n"
            "重要规则：\n"
            "1. 根据科室特点给出针对性建议（如消化科可能需空腹，骨科可能需带片子）\n"
            "2. 提醒必须携带的证件和材料\n"
            "3. 给出着装和饮食建议\n"
            "4. 根据患者年龄给出额外提醒（老人/儿童的特殊注意事项）\n"
            "5. 语气亲切、实用，按条目列出\n\n"
            "请以JSON格式输出，包含以下字段：\n"
            "- documents: 需携带的证件材料列表\n"
            "- diet_before: 就诊前饮食注意事项\n"
            "- clothing: 着装建议\n"
            "- special_notes: 特别提醒（针对老人/儿童/特定检查）\n"
            "- checklist: 完整准备清单（字符串，每行一项）"
        )

    async def process(self, user_input: str, context: dict = None) -> dict:
        """生成准备清单"""
        department = (context or {}).get("department", "内科")
        age = (context or {}).get("patient_age", 30)
        gender = (context or {}).get("patient_gender", "未知")
        urgency = (context or {}).get("urgency_level", "normal")

        age_group = "儿童" if age and age < 14 else ("老人" if age and age >= 60 else "成人")

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", (
                "就诊信息：\n"
                "- 推荐科室：{department}\n"
                "- 患者年龄：{age}岁（{age_group}）\n"
                "- 患者性别：{gender}\n"
                "- 紧急程度：{urgency}\n\n"
                "请生成针对性的就医准备清单。只返回JSON对象，不要加markdown代码块。"
            )),
        ])

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "department": department,
            "age": age,
            "age_group": age_group,
            "gender": gender,
            "urgency": urgency,
        })

        # 解析结果
        documents = []
        diet_before = ""
        clothing = ""
        special_notes = []
        checklist = ""

        try:
            if "{" in result:
                json_str = result[result.index("{"):result.rindex("}") + 1]
                data = json.loads(json_str)
                documents = data.get("documents", [])
                diet_before = data.get("diet_before", "")
                clothing = data.get("clothing", "")
                special_notes = data.get("special_notes", [])
                checklist = data.get("checklist", "")
        except Exception:
            pass

        return {
            "reply": f"为您整理了前往 **{department}** 就诊的准备事项：\n\n{checklist}",
            "meta_data": {
                "documents": documents,
                "diet_before": diet_before,
                "clothing": clothing,
                "special_notes": special_notes,
                "checklist": checklist,
                "department": department,
                "age_group": age_group,
            },
        }
