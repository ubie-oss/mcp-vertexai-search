# MCP Server for Vertex AI Search

This is a MCP server to search documents using Vertex AI.

## Architecture

This solution uses Gemini with Vertex AI grounding to search documents using your private data.
Grounding improves the quality of search results by grounding Gemini's responses in your data stored in Vertex AI Datastore.
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

```bash
uv run mcp-vertexai-search serve \
    --model_project <your-gemini-project-id> \
    --model_location <your-gemini-location> \
    --datastore_project <your-datastore-project-id> \
    --datastore_location <your-datastore-location> \
    --datastore_id <your-datastore-id> \
    --transport <stdio|sse>
```

## Roadmap

- [ ] Config file to tune the MCP server
- [ ] Multiple Vertex AI data stores
