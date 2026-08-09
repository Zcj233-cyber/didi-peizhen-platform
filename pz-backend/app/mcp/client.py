"""MCP 进程内门面 - 供内部 Agent 直接调用工具

Agent 用法：
    from app.mcp import client as mcp
    hospitals = mcp.search_hospitals(city="武汉")["hospitals"]
    weather = await mcp.get_weather("北京")

工具函数与 MCP Server 注册的是同一批函数对象（唯一来源在 tools.py），
不会出现"Server 一份、Agent 另一份"的漂移。
"""
from .tools import (
    TOOL_REGISTRY,
    search_hospitals,
    list_companions,
    list_services,
    get_user_orders,
    search_faq,
    get_business_stats,
    get_weather,
    get_travel_advice,
    calc_distance,
    get_static_map_url,
    get_hospital_image,
)

__all__ = [
    "search_hospitals",
    "list_companions",
    "list_services",
    "get_user_orders",
    "search_faq",
    "get_business_stats",
    "get_weather",
    "get_travel_advice",
    "calc_distance",
    "get_static_map_url",
    "get_hospital_image",
    "call_tool",
]

# 名称 → 函数 索引，供 call_tool 按名调用
TOOL_INDEX = {name: fn for name, fn, _ in TOOL_REGISTRY}


def call_tool(name: str, **kwargs):
    """按工具名调用。若函数为 async，返回 awaitable，由调用方 await。"""
    fn = TOOL_INDEX.get(name)
    if fn is None:
        raise KeyError(f"未知的 MCP 工具: {name}")
    return fn(**kwargs)
