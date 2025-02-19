# MCP Server for Vertex AI Search

This is a MCP server to search documents using Vertex AI.

## Architecture

This solution uses Gemini with Vertex AI grounding to search documents using your private data.
Grounding improves the quality of search results by grounding Gemini's responses in your data stored in Vertex AI Datastore.
We can integrate one or multiple Vertex AI data stores to the MCP server.
For more details on grounding, refer to [Vertex AI Grounding Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/ground-with-your-data).

![Architecture](./docs/img//archirecture.png)

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Vertex AI data store
  - Please look into [the official documentation about data stores](https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest) for more information

### Set up Local Environment

```shell
# Optional: Install uv
python -m pip install -r requirements.setup.txt

# Create a virtual environment
uv venv
uv sync --all-extras
```

### Run the MCP server

This supports two transports for SSE (Server-Sent Events) and stdio (Standard Input Output).
We can control the transport by setting the `--transport` flag.

We can configure the MCP server with a YAML file.
[config.yml.template](./config.yml.template) is a template for the config file.
Please modify the config file to fit your needs.

```bash
uv run mcp-vertexai-search serve \
    --config config.yml \
    --transport <stdio|sse>
```

### Test the Vertex AI Search

We can test the Vertex AI Search by using the `mcp-vertexai-search search` command without the MCP server.

```bash
uv run mcp-vertexai-search search \
    --config config.yml \
    --query <your-query>
```

## Appendix A: Config file

[config.yml.template](./config.yml.template) is a template for the config file.

- `server`
  - `server.name`: The name of the MCP server
- `model`
  - `model.model_name`: The name of the Vertex AI model
  - `model.project_id`: The project ID of the Vertex AI model
  - `model.location`: The location of the model (e.g. us-central1)
  - `model.impersonate_service_account`: The service account to impersonate
  - `model.generate_content_config`: The configuration for the generate content API
- `data_stores`: The list of Vertex AI data stores
  - `data_stores.project_id`: The project ID of the Vertex AI data store
  - `data_stores.location`: The location of the Vertex AI data store (e.g. us)
  - `data_stores.datastore_id`: The ID of the Vertex AI data store
  - `data_stores.tool_name`: The name of the tool
  - `data_stores.description`: The description of the Vertex AI data store
