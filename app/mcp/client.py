"""
MCP Client Manager - 管理 MCP 服务器连接

通过 MultiServerMCPClient 以 stdio 方式启动 MCP 服务器子进程，
获取 LangChain 兼容的工具对象供 Agent 使用。
"""
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys
import os
import logging

logger = logging.getLogger(__name__)


class MCPClientManager:
    """MCP 客户端管理器（全局单例）"""

    def __init__(self):
        self._client = None

    def init(self):
        """初始化 MCP 客户端连接配置"""
        server_script = os.path.join(
            os.path.dirname(__file__), "server.py"
        )

        self._client = MultiServerMCPClient({
            "travel-tools": {
                "command": sys.executable,
                "args": [server_script],
                "transport": "stdio",
            }
        })
        logger.info("MCP client manager initialized")

    async def get_tools(self):
        """
        获取 MCP 服务器提供的工具（返回 LangChain Tool 对象列表）

        注意：每次调用会为新工具创建独立的 stdio session（子进程），
        调用完毕后自动关闭，无需手动管理生命周期。
        """
        if not self._client:
            self.init()

        tools = await self._client.get_tools()
        logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")
        return tools


# 全局 MCP 客户端管理器实例
mcp_client_manager = MCPClientManager()
