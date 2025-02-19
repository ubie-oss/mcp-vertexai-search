import asyncio

import click
import vertexai

from mcp_vertexai_search.agent import (
    VertexAISearchAgent,
    create_model,
    create_vertex_ai_tools,
    get_default_safety_settings,
    get_generation_config,
    get_system_instruction,
)
from mcp_vertexai_search.config import load_yaml_config
from mcp_vertexai_search.server import create_server, run_sse_server, run_stdio_server

cli = click.Group()


@cli.command("serve")
# trunk-ignore(bandit/B104)
@click.option("--host", type=str, default="0.0.0.0", help="The host to listen on")
@click.option("--port", type=int, default=8080, help="The port to listen on")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="The transport to use",
)
@click.option("--config", type=click.Path(exists=True), help="The config file")
def serve(
    host: str,
    port: int,
    transport: str,
    config: str,
):
    server_config = load_yaml_config(config)
    vertexai.init(
        project=server_config.model.project_id, location=server_config.model.location
    )

    search_tools = create_vertex_ai_tools(server_config.data_stores)
    model = create_model(
        model_name=server_config.model.model_name,
        tools=search_tools,
        system_instruction=get_system_instruction(),
    )
    agent = VertexAISearchAgent(model=model)

    app = create_server(agent, server_config)
    if transport == "stdio":
        asyncio.run(run_stdio_server(app))
    elif transport == "sse":
        asyncio.run(run_sse_server(app, host, port))
    else:
        raise ValueError(f"Invalid transport: {transport}")


@cli.command("search")
@click.option("--config", type=click.Path(exists=True), help="The config file")
@click.option("--query", type=str, help="The query to search for")
def search(
    config: str,
    query: str,
):
    # Load the config
    server_config = load_yaml_config(config)

    # Initialize the Vertex AI client
    vertexai.init(
        project=server_config.model.project_id, location=server_config.model.location
    )

    # Create the search agent
    search_tools = create_vertex_ai_tools(server_config.data_stores)
    model = create_model(
        model_name=server_config.model.model_name,
        tools=search_tools,
        system_instruction=get_system_instruction(),
    )
    agent = VertexAISearchAgent(
        model=model,
    )

    # Generate the response
    generation_config = get_generation_config()
    safety_settings = get_default_safety_settings()
    response = agent.search(
        query,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    print(response)
