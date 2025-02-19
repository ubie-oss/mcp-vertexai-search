from typing import Dict, List

from mcp import types as mcp_types

from mcp_vertexai_search.config import DataStoreConfig


def to_mcp_tool(tool_name: str, description: str) -> mcp_types.Tool:
    """Convert a tool name and description to an MCP Tool"""
    return mcp_types.Tool(
        name=tool_name,
        description=description,
        inputSchema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": """\
                      A natural language question, not search keywords, used to query the documents.
                      The query question should be sentence(s), not search keywords.
                      """.strip(),
                },
            },
        },
    )


def to_mcp_tools_map(
    data_store_configs: List[DataStoreConfig],
) -> Dict[str, mcp_types.Tool]:
    """Convert a list of DataStoreConfigs to a tool map"""
    return {
        data_store_config.tool_name: to_mcp_tool(
            data_store_config.tool_name, data_store_config.description
        )
        for data_store_config in data_store_configs
    }
