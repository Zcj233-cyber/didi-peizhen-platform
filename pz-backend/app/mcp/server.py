"""MCP Server - 对外提供 streamable HTTP 端点

工具定义唯一来源是 tools.py 的 TOOL_REGISTRY，这里遍历注册进 FastMCP。
外部客户端（Claude Desktop / Cursor / MCP Inspector / 自定义 client）连接：
    http://localhost:2306/v3pz/mcp/   （注意带尾斜杠）
"""
from mcp.server.fastmcp import FastMCP

from .tools import TOOL_REGISTRY


def _create_server() -> FastMCP:
    server = FastMCP(
        "pz-medical",
        instructions="医疗陪诊平台数据工具集：医院/陪诊师/服务/订单/FAQ/运营统计/天气/地图/距离",
        streamable_http_path="/",  # 配合外层 mount /v3pz/mcp，客户端用 /v3pz/mcp/
    )
    for name, fn, description in TOOL_REGISTRY:
        server.add_tool(fn, name=name, description=description)
    return server


# 模块级单例：Server 与 ASGI app 各创建一次，会话管理器复用
mcp = _create_server()
mcp_app = mcp.streamable_http_app()
