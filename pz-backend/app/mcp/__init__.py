"""内部统一工具层模块（按 MCP 工具规范组织，不对外暴露网络端点）

- tools.py   纯工具函数 + TOOL_REGISTRY（工具唯一来源）
- client.py  进程内门面，供内部 Agent 直接调用工具
"""
