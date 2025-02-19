
import textwrap

import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.shared.exceptions import ErrorData, McpError

from mcp_vertexai_search.agent import (
    VertexAISearchAgent,
    get_default_generation_config,
    get_default_safety_settings,
)

# class VertexAISearchServer:
#     agent: VertexAISearchAgent

#     def __init__(self, agent: VertexAISearchAgent):
#         self.agent = agent
#         self.app: Optional[Server] = None

#     def create_app(self) -> Server:
#         app = Server("vertexai_search")

#         @app.call_tool()
#         async def call_tool(
#             name: str, arguments: dict
#         ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
#             if name != "vertexai_search":
#                 raise McpError(
#                     ErrorData(
#                         code=types.INVALID_PARAMS, message=f"Unknown tool: {name}"
#                     )
#                 )
#             if "query" not in arguments:
#                 raise McpError(
#                     ErrorData(code=types.INVALID_PARAMS, message="query is required")
#                 )
#             generation_config = generative_models.GenerationConfig(
#                 temperature=0.2,
#                 top_p=0.95,
#             )
#             safety_settings = [
#                 generative_models.SafetySetting(
#                     category=generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
#                     threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
#                 ),
#                 generative_models.SafetySetting(
#                     category=generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
#                     threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
#                 ),
#                 generative_models.SafetySetting(
#                     category=generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
#                     threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
#                 ),
#                 generative_models.SafetySetting(
#                     category=generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT,
#                     threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
#                 ),
#             ]
#             response = self.agent.search(
#                 query=arguments["query"],
#                 generation_config=generation_config,
#                 safety_settings=safety_settings,
#             )
#             return [types.TextContent(type="text", text=response)]


def create_server(
    agent: VertexAISearchAgent,
) -> Server:
    """Create the MCP server."""
    app = Server("vertexai_search")

    @app.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return [
            types.Prompt(
                name="vertexai_search",
                description="Searches technical documents using Vertex AI Search",
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name != "vertexai_search":
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
            generation_config = get_default_generation_config()
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
        return [
            types.Tool(
                name="vertexai_search",
                description="Searches a website using Vertex AI Search",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        },
                    },
                },
            )
        ]

    return app


def run_stdio_server(app: Server) -> None:
    """Run the server using the stdio transport."""
    try:
        from mcp.server.stdio import stdio_server
    except ImportError as e:
        raise ImportError("stdio transport is not available") from e

    async def arun():
        async with stdio_server() as streams:
            print("Running server...")
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
