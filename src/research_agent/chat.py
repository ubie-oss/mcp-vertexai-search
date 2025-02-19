import argparse
import asyncio

from google import genai
from google.genai import chats, types
from loguru import logger

from research_agent.mcp_client import MCPClient
from research_agent.utils import to_gemini_tool


async def process_query(
    chat_client: chats.Chat,
    mcp_client: MCPClient,
    query: str,
):
    """Process the user query using Gemini and MCP tools."""
    response = chat_client.send_message(message=[query])
    if not response.candidates:
        raise RuntimeError("No response from Gemini")

    returned_message = None
    for candidate in response.candidates:
        if candidate.content:
            for part in candidate.content.parts:
                # If the candidate is a text, add it to the returned message
                if part.text:
                    returned_message = types.Content(
                        role="model", parts=[types.Part.from_text(text=part.text)]
                    )
                # If the candidate is a tool call, call the tool
                elif part.function_call:
                    tool_name = part.function_call.name
                    tool_args = part.function_call.args
                    logger.debug(f"Tool name: {tool_name}, tool args: {tool_args}")
                    tool_call = await mcp_client.call_tool(tool_name, tool_args)
                    if tool_call and tool_call.content:
                        returned_message = types.Content(
                            role="model",
                            parts=[
                                types.Part.from_text(text=content.text)
                                for content in tool_call.content
                            ],
                        )
                    else:
                        raise RuntimeError(f"No tool call content {tool_call}")
                else:
                    raise RuntimeError(f"Unknown part type {part}")
    return returned_message


async def chat(server_url: str):
    """
    Run the chat server.
    """
    # Why do we use google-genai, not vertexai?
    # Because it is easier to convert MCP tools to GenAI tools in google-genai.
    genai_client = genai.Client(vertexai=True, location="us-central1")
    mcp_client = MCPClient(name="document-search")
    await mcp_client.connect_to_server(server_url=server_url)

    # Collect tools from MCP server
    mcp_tools = await mcp_client.list_tools()
    # Convert MCP tools to GenAI tools
    genai_tools = [to_gemini_tool(tool) for tool in mcp_tools.tools]

    # Create chat client
    chat_client = genai_client.chats.create(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            tools=genai_tools,
            system_instruction="""
            You are a helpful assistant to search documents.
            You have to pass the query to the tool to search the documents as much natural as possible.
          """,
        ),
    )

    print("If you want to quit, please enter 'bye'")
    try:
        while True:
            # Get user query
            query = input("Enter your query: ")
            if query == "bye":
                break

            # Get response from GenAI
            response = await process_query(chat_client, mcp_client, query)
            print(response)
    # pylint: disable=broad-except
    except Exception as e:
        await mcp_client.cleanup()
        raise RuntimeError from e


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    # trunk-ignore(bandit/B104)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    # Run the chat server
    server_url = f"http://{args.host}:{args.port}/sse"
    asyncio.run(chat(server_url))
