"""MCP（Model Context Protocol）模块

- tools.py   纯工具函数 + TOOL_REGISTRY（工具唯一来源）
- server.py  FastMCP Server，注册 tools.py 中的全部工具，对外提供 streamable HTTP 端点
- client.py  进程内门面，供内部 Agent 直接调用工具
"""
