"""真实 Agent/编排代码配模型与工具替身；禁止连接真实数据库或 API。"""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from langchain_core.runnables import RunnableLambda
from app.agents.base import BaseAgent
from app.agents.visit_planner import VisitPlannerOrchestrator
from app.mcp import client as mcp


def hospital(name, rank, city="广州", hid=1):
    return dict(id=hid, name=name, rank=rank, city=city, label="", intro="", address="测试地址",
                latitude="", longitude="", avatar_url="")


class PlannerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.outputs = {
            "triage": dict(recommended_department="消化内科", urgency_level="normal", symptom_summary="测试摘要"),
            "hospital_advisor": dict(recommended_hospitals=[dict(name="医院B", rank="模型编造等级", reason="测试理由")], best_choice="医院B", summary="测试推荐"),
            "prep_guide": dict(documents=["身份证"], checklist="携带身份证", special_notes=[]),
            "cost_estimator": dict(total_range="模型参考区间", companion_fee="模型错误价9999元", breakdown=[]),
            "synthesis": dict(title="测试攻略", summary="测试汇总", guide_sections=[dict(title="攻略", content="已有信息")]),
        }
        self.failures, self.prompts, self.events = {}, {}, []
        self.hospitals = [hospital("医院A", "三甲"), hospital("医院B", "二甲", hid=2)]
        self.city_candidates = lambda **kwargs: {"hospitals": self.hospitals}
        self.search = Mock(side_effect=lambda **kwargs: self.city_candidates(**kwargs))
        self.companions = Mock(return_value={"companions": []})
        self.services = Mock(return_value={"services": [dict(name="测试陪诊", price=88.0)]})
        self.weather = AsyncMock(return_value=dict(condition="晴", temperature=20, wind="2级", source="realtime"))
        self.advice = Mock(return_value={"advice": "测试出行文案"})
        self.patches = [
            patch.object(BaseAgent, "_load_config", lambda agent: {"system_prompt": agent._default_system_prompt()}),
            patch.object(BaseAgent, "_init_llm", lambda agent: self.fake_model(agent)),
            patch.object(mcp, "search_hospitals", self.search),
            patch.object(mcp, "list_companions", self.companions),
            patch.object(mcp, "list_services", self.services),
            patch.object(mcp, "get_weather", self.weather),
            patch.object(mcp, "get_travel_advice", self.advice),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.planner = VisitPlannerOrchestrator(stage_timeout=2)

    def fake_model(self, agent):
        async def invoke(prompt):
            name = agent.agent_type
            self.prompts.setdefault(name, []).append(prompt.to_string())
            self.events.append(name + ":start")
            failure = self.failures.get(name)
            if callable(failure):
                await failure()
            elif failure:
                raise RuntimeError("synthetic failure")
            output = self.outputs[name]
            self.events.append(name + ":done")
            return output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        return RunnableLambda(invoke)

    async def plan(self):
        return await self.planner.plan("测试输入", patient_age=30, city="广州")

    async def test_success_queries_once_and_cost_uses_selected_hospital(self):
        result = await self.plan()
        self.assertEqual(result["planning_status"], "complete")
        self.assertEqual(result["warnings"], [])
        self.search.assert_called_once_with(city="广州", limit=100)
        self.weather.assert_awaited_once_with("广州")
        self.companions.assert_not_called()
        self.assertNotIn("医院A", self.prompts["triage"][0])
        self.assertIn("医院B", self.prompts["cost_estimator"][0])
        self.assertIn("二甲", self.prompts["cost_estimator"][0])
        self.assertNotIn("模型编造等级", self.prompts["cost_estimator"][0])
        self.assertLess(self.events.index("hospital_advisor:done"), self.events.index("cost_estimator:start"))
        self.assertEqual(result["hospitals"]["recommended"][0]["rank"], "二甲")
        self.assertEqual(result["cost_estimate"]["hospital_name"], "医院B")
        self.assertEqual(result["cost_estimate"]["companion_fee"], "88元")

    async def test_hospital_preparation_weather_actually_overlap(self):
        started = set()
        barrier = asyncio.Event()
        async def arrive(name):
            started.add(name)
            if len(started) == 3:
                barrier.set()
            await asyncio.wait_for(barrier.wait(), 1)
        self.failures["hospital_advisor"] = lambda: arrive("hospital")
        self.failures["prep_guide"] = lambda: arrive("prep")
        async def weather(city):
            await arrive("weather")
            return dict(condition="晴", temperature=20, source="realtime")
        self.weather.side_effect = weather
        result = await self.plan()
        self.assertEqual(started, {"hospital", "prep", "weather"})
        self.assertEqual(result["planning_status"], "complete")

    async def test_each_noncritical_failure_preserves_successful_parts(self):
        for name, warning in [("hospital_advisor", "医院推荐"), ("prep_guide", "准备清单"), ("cost_estimator", "费用预估"), ("synthesis", "攻略整理")]:
            with self.subTest(stage=name):
                self.failures = {name: True}
                result = await self.plan()
                self.assertEqual(result["planning_status"], "partial")
                self.assertTrue(any(warning in w for w in result["warnings"]))
                self.assertEqual(result["triage"]["recommended_department"], "消化内科")
                self.assertTrue(result["guide_sections"])
                if name == "synthesis":
                    self.assertIn("医院B", str(result["guide_sections"]))
                if name == "hospital_advisor":
                    self.assertEqual(result["cost_estimate"]["total_range"], "")

    async def test_invalid_json_is_partial_instead_of_silent_success(self):
        for name in ("hospital_advisor", "prep_guide", "cost_estimator", "synthesis"):
            with self.subTest(stage=name):
                original = self.outputs[name]
                self.outputs[name] = "broken JSON"
                try:
                    result = await self.plan()
                    self.assertEqual(result["planning_status"], "partial")
                    self.assertTrue(result["warnings"])
                finally:
                    self.outputs[name] = original

    async def test_invalid_field_types_or_empty_results_are_partial(self):
        cases = [
            ("hospital_advisor", {"recommended_hospitals": "wrong type"}),
            ("prep_guide", {"checklist": "清单", "documents": [{}]}),
            ("prep_guide", {"checklist": ""}),
            ("cost_estimator", {"total_range": None}),
            ("cost_estimator", {"total_range": "参考", "breakdown": "wrong type"}),
            ("cost_estimator", {"total_range": "参考", "breakdown": [{"range": 123}]}),
            ("synthesis", {"guide_sections": []}),
            ("synthesis", {"guide_sections": [{"title": "标题", "content": None}]}),
        ]
        for name, output in cases:
            with self.subTest(stage=name, output=output):
                original = self.outputs[name]
                self.outputs[name] = output
                try:
                    result = await self.plan()
                    self.assertEqual(result["planning_status"], "partial")
                    self.assertTrue(result["warnings"])
                finally:
                    self.outputs[name] = original

    async def test_real_route_returns_partial_result_and_explicit_503(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routers import agents as routes
        app = FastAPI()
        app.include_router(routes.router)
        with patch.object(routes, "visit_planner", self.planner), patch.object(routes, "verify_h5_token", return_value={"user_id": 1}):
            with TestClient(app) as client:
                self.failures["prep_guide"] = True
                response = client.post('/agent/visit-plan', json={"symptoms": "测试输入", "city": "广州"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["code"], 10000)
                self.assertEqual(response.json()["data"]["planning_status"], "partial")
                self.failures = {"triage": True}
                response = client.post('/agent/visit-plan', json={"symptoms": "测试输入", "city": "广州"})
                self.assertEqual(response.status_code, 503)
                self.assertIn("未生成就医攻略", response.json()["detail"])

    async def test_triage_failure_or_invalid_urgency_stops_plan(self):
        for output in ("broken JSON", dict(recommended_department="消化内科", urgency_level="invalid")):
            self.outputs["triage"] = output
            with self.assertRaises(HTTPException) as raised:
                await self.plan()
            self.assertEqual(raised.exception.status_code, 503)
        self.search.assert_not_called()
        self.weather.assert_not_awaited()

    async def test_timeout_cancels_branch_and_preserves_other_results(self):
        cancelled = asyncio.Event()
        async def hang():
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        self.failures["prep_guide"] = hang
        self.planner.stage_timeout = 0.5
        result = await self.plan()
        self.assertTrue(cancelled.is_set())
        self.assertEqual(result["planning_status"], "partial")
        self.assertEqual(result["hospitals"]["best_choice"], "医院B")
        self.assertTrue(result["cost_estimate"]["total_range"])

    async def test_no_hospitals_skips_cost_without_inventing_grade(self):
        self.hospitals = []
        result = await self.plan()
        self.assertEqual(result["hospitals"]["list"], [])
        self.assertEqual(result["cost_estimate"]["hospital_rank"], "")
        self.assertNotIn("cost_estimator", self.prompts)
        self.assertNotIn("hospital_advisor", self.prompts)
        self.assertEqual(self.search.call_count, 2)  # city lookup + nationwide fallback

    async def test_missing_rank_skips_cost(self):
        self.hospitals[1]["rank"] = ""
        result = await self.plan()
        self.assertEqual(result["hospitals"]["best_choice"], "医院B")
        self.assertNotIn("cost_estimator", self.prompts)
        self.assertIn("费用预估暂不可用", result["warnings"])

    async def test_nationwide_fallback_uses_actual_hospital_city(self):
        self.hospitals[1]["city"] = "深圳"
        self.city_candidates = lambda **kwargs: {"hospitals": [] if kwargs.get("city") else self.hospitals}
        result = await self.plan()
        self.assertEqual(result["cost_estimate"]["city"], "深圳")
        self.assertIn("深圳", self.prompts["cost_estimator"][0])

    async def test_simulated_or_failed_weather_never_displays_fake_temperature(self):
        for source in ("simulated", "error"):
            with self.subTest(source=source):
                if source == "error":
                    self.weather.side_effect = RuntimeError("synthetic weather failure")
                else:
                    self.weather.return_value = dict(condition="晴", temperature=99, source=source)
                result = await self.plan()
                self.assertEqual(result["weather"]["source"], "unavailable")
                self.assertEqual(result["weather"]["temperature"], "")
                self.assertEqual(result["planning_status"], "partial")
                self.assertNotIn("99", self.prompts["synthesis"][-1])

    async def test_standalone_triage_keeps_existing_lists_and_weather(self):
        result = await self.planner.triage_agent.process("测试输入", {"city": "广州"})
        self.search.assert_called_once_with(limit=200)
        self.companions.assert_called_once_with(active_only=True, limit=200)
        self.weather.assert_awaited_once_with("广州")
        self.assertEqual(len(result["meta_data"]["recommended_hospitals"]), 2)

    async def test_invalid_hospital_name_is_not_used_as_cost_basis(self):
        self.outputs["hospital_advisor"]["recommended_hospitals"] = [dict(name="不存在的医院")]
        result = await self.plan()
        self.assertEqual(result["hospitals"]["list"], [])
        self.assertNotIn("cost_estimator", self.prompts)

    async def test_request_cancellation_cancels_parallel_branches(self):
        started, stopped = set(), set()
        ready = asyncio.Event()
        async def hang(name):
            started.add(name)
            if len(started) == 3:
                ready.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.add(name)
        self.failures["hospital_advisor"] = lambda: hang("hospital")
        self.failures["prep_guide"] = lambda: hang("prep")
        async def weather(city): return await hang("weather")
        self.weather.side_effect = weather
        task = asyncio.create_task(self.plan())
        await asyncio.wait_for(ready.wait(), 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(stopped, started)
        self.assertNotIn("synthesis", self.prompts)


if __name__ == "__main__":
    unittest.main()
