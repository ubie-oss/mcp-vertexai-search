from google import genai
from google.genai import types as genai_types
from mcp import types as mcp_types


def to_gemini_tool(mcp_tool: mcp_types.Tool) -> genai_types.Tool:
    """
    Converts an MCP tool schema to a Gemini tool.

    Args:
        name: The name of the tool.
        description: The description of the tool.
        input_schema: The input schema of the tool.

    Returns:
        A Gemini tool.
    """
    required_params: list[str] = mcp_tool.inputSchema.get("required", [])
    properties = {}
    for key, value in mcp_tool.inputSchema.get("properties", {}).items():
        schema_dict = {
            "type": value.get("type", "STRING").upper(),
            "description": value.get("description", ""),
        }
        properties[key] = genai_types.Schema(**schema_dict)

    function = genai.types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description,
        parameters=genai.types.Schema(
            type="OBJECT",
            properties=properties,
            required=required_params,
        ),
    )
    return genai_types.Tool(function_declarations=[function])
