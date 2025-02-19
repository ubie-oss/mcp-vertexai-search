from contextlib import AsyncExitStack
from typing import Optional

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    def __init__(self, name: str,server_url: Optional[str] = None):
        # Initialize session and client objects
        self.name = name
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        if server_url:
            self.connect_to_server(server_url)

    async def connect_to_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Use AsyncExitStack to manage the contexts
        _sse_client = sse_client(url=server_url)
        streams = await self.exit_stack.enter_async_context(_sse_client)

        _session_context = ClientSession(*streams)
        self.session: ClientSession = await self.exit_stack.enter_async_context(
            _session_context
        )

        # Initialize
        await self.session.initialize()

    async def cleanup(self):
        """Properly clean up the session and streams"""
        await self.exit_stack.aclose()

    async def list_tools(self):
        return await self.session.list_tools()

    async def call_tool(self, tool_name: str, tool_arguments: Optional[dict] = None):
        return await self.session.call_tool(tool_name, tool_arguments)


if __name__ == "__main__":

    async def main():
        client = MCPClient()
        await client.connect_to_server(server_url="http://0.0.0.0:8080/sse")
        tools = await client.list_tools()
        print(tools)
        tool_call = await client.call_tool("document-search", {"query": "cpp segment とはなんですか？"})
        print(tool_call)
        await client.cleanup()  # Ensure cleanup is called

    import asyncio

    asyncio.run(main())
