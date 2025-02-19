import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.shared.exceptions import ErrorData, McpError

from mcp_vertexai_search.agent import (
    VertexAISearchAgent,
    get_default_safety_settings,
    get_generation_config,
)
from mcp_vertexai_search.config import Config
from mcp_vertexai_search.utils import to_mcp_tools_map


def create_server(
    agent: VertexAISearchAgent,
    config: Config,
) -> Server:
    """Create the MCP server."""
    app = Server("document-search")

    # Create a map of tools for the MCP server
    tools_map = to_mcp_tools_map(config.data_stores)

    # TODO Add @app.list_prompts()

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name not in tools_map:
            raise McpError(
                ErrorData(code=types.INVALID_PARAMS, message=f"Unknown tool: {name}")
            )
        if "query" not in arguments:
            raise McpError(
                ErrorData(code=types.INVALID_PARAMS, message="query is required")
            )
        # pylint: disable=broad-exception-caught
        try:
            # TODO handle retry logic
            generation_config = get_generation_config(
                temperature=config.model.generate_content_config.temperature,
                top_p=config.model.generate_content_config.top_p,
            )
            safety_settings = get_default_safety_settings()
            response = agent.search(
                query=arguments["query"],
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            return [types.TextContent(type="text", text=response)]
        # pylint: disable=broad-exception-caught
        except Exception as e:
            raise McpError(ErrorData(code=types.INVALID_PARAMS, message=str(e))) from e

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [tools_map[tool_name] for tool_name in tools_map]

    return app


def run_stdio_server(app: Server) -> None:
    """Run the server using the stdio transport."""
    try:
        from mcp.server.stdio import stdio_server
    except ImportError as e:
        raise ImportError("stdio transport is not available") from e

    async def arun():
        async with stdio_server() as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    anyio.run(arun)


def run_sse_server(app: Server, host: str, port: int) -> None:
    """Run the server using the SSE transport."""
    try:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
    except ImportError as e:
        raise ImportError("SSE transport is not available") from e

    # Handle SSE connections
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    # Create the Starlette app
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    # Serve the Starlette app
    uvicorn.run(starlette_app, host=host, port=port)
