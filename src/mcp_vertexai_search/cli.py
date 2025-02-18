import asyncio

import click
import vertexai

from mcp_vertexai_search.agent import (
    VertexAISearchAgent,
    create_model,
    create_vertexai_search_tool,
    get_default_generation_config,
    get_default_safety_settings,
    get_system_instruction,
)
from mcp_vertexai_search.server import create_server, run_sse_server, run_stdio_server

cli = click.Group()


# bandit: ignore=B104
@cli.command("serve")
@click.option("--host", type=str, default="0.0.0.0", help="The host to listen on")
@click.option("--port", type=int, default=8080, help="The port to listen on")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="The transport to use",
)
@click.option("--model_project_id", type=str, help="The project ID")
@click.option("--model_location", type=str, help="The location")
@click.option("--model_name", type=str, help="The model name", default="models/gemini-1.5-flash-002")
@click.option("--datastore_project_id", type=str, help="The datastore project ID")
@click.option("--datastore_location", type=str, help="The datastore location")
@click.option("--datastore_id", type=str, help="The datastore ID")
def serve(
    host: str,
    port: int,
    transport: str,
    model_project_id: str,
    model_location: str,
    model_name: str,
    datastore_project_id: str,
    datastore_location: str,
    datastore_id: str,
):
    vertexai.init(project=model_project_id, location=model_location)

    search_tool = create_vertexai_search_tool(
        project_id=datastore_project_id,
        location=datastore_location,
        datastore_id=datastore_id,
    )
    model = create_model(
        model_name=model_name,
        tools=[search_tool],
        system_instruction=get_system_instruction(),
    )
    agent = VertexAISearchAgent(model=model)
    app = create_server(agent)
    if transport == "stdio":
        asyncio.run(run_stdio_server(app))
    elif transport == "sse":
        asyncio.run(run_sse_server(app, host, port))
    else:
        raise ValueError(f"Invalid transport: {transport}")


@cli.command("search")
@click.option("--model_project_id", type=str, help="The project ID")
@click.option("--model_location", type=str, help="The location")
@click.option("--model_name", type=str, help="The model name", required=False, default="models/gemini-1.5-flash-002")
@click.option("--datastore_project_id", type=str, help="The datastore project ID")
@click.option("--datastore_location", type=str, help="The datastore location")
@click.option("--datastore_id", type=str, help="The datastore ID")
@click.option("--query", type=str, help="The query to search for")
def search(
    model_project_id: str,
    model_location: str,
    model_name: str,
    datastore_project_id: str,
    datastore_location: str,
    datastore_id: str,
    query: str,
):
    vertexai.init(project=model_project_id, location=model_location)
    search_tool = create_vertexai_search_tool(
        project_id=datastore_project_id,
        location=datastore_location,
        datastore_id=datastore_id,
    )
    model = create_model(
        model_name=model_name,
        tools=[search_tool],
        system_instruction=get_system_instruction(),
    )
    agent = VertexAISearchAgent(
        model=model,
    )
    generation_config = get_default_generation_config()
    safety_settings = get_default_safety_settings()
    response = agent.search(
        query,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    print(response)
