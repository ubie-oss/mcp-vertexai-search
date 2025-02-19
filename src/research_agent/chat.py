import argparse
import asyncio
import json
import textwrap
from typing import List

from google import genai
from google.genai import chats, types
from loguru import logger
from pydantic import BaseModel, Field

from research_agent.mcp_client import MCPClient
from research_agent.utils import to_gemini_tool


class Reference(BaseModel):
    """A reference to a document."""

    title: str = Field(..., description="The title of the document.")
    raw_text: str = Field(..., description="The raw text of the document.")


class SearchResponse(BaseModel):
    """The response from the search tool."""

    answer: str = Field(..., description="The answer to the user's question.")
    references: List[Reference] = Field(
        ...,
        description="The references to the documents that are used to answer the user's question.",
    )

    @classmethod
    def from_json_string(cls, json_string: str) -> "SearchResponse":
        """Deserialize the search response from a JSON string."""
        return cls(**json.loads(json_string))

    def __str__(self) -> str:
        return textwrap.dedent(f"""
Answer: {self.answer}

References:
{"\n".join([f"  - {ref.title}: {ref.raw_text}" for ref in self.references])}
""")


async def process_query(
    chat_client: chats.Chat,
    mcp_client: MCPClient,
    query: str,
) -> str:
    """Process the user query using Gemini and MCP tools."""
    response = chat_client.send_message(message=[query])
    if not response.candidates:
        raise RuntimeError("No response from Gemini")

    response_text = []
    for candidate in response.candidates:
        if not candidate.content:
            logger.debug(f"No content in candidate {candidate}")
            continue

        for part in candidate.content.parts:
            if part.text:
                response_text.append(part.text)
            elif part.function_call:
                tool_name = part.function_call.name
                tool_args = part.function_call.args
                logger.debug(f"Tool name: {tool_name}, tool args: {tool_args}")
                tool_call = await mcp_client.call_tool(tool_name, tool_args)

                if tool_call and tool_call.content:
                    for content in tool_call.content:
                        text = content.text
                        if not text:
                            logger.info(f"No text in tool call content {content}")
                            continue

                        try:
                            parsed_content = SearchResponse.from_json_string(text)
                            response_text.append(str(parsed_content))
                        except Exception as e:  # pylint: disable=broad-except
                            logger.error(
                                f"Failed to deserialize tool call content {content}: {e}"
                            )
                            response_text.append(text)
                else:
                    raise RuntimeError(f"No tool call content {tool_call}")
            else:
                raise RuntimeError(f"Unknown part type {part}")
    return "\n".join(response_text)


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
