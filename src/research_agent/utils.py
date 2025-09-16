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
    function_declaration = to_gemini_function_declarations(mcp_tool)
    return genai_types.Tool(function_declarations=[function_declaration])


def to_gemini_function_declarations(
    mcp_tool: mcp_types.Tool,
) -> genai_types.FunctionDeclarationDict:
    required_params: list[str] = mcp_tool.inputSchema.get("required", [])
    properties = {}
    for key, value in mcp_tool.inputSchema.get("properties", {}).items():
        schema_dict = {
            "type": value.get("type", "STRING").upper(),
            "description": value.get("description", ""),
        }
        properties[key] = genai_types.SchemaDict(**schema_dict)

    function_declaration = genai_types.FunctionDeclarationDict(
        name=mcp_tool.name,
        description=mcp_tool.description,
        parameters=genai_types.SchemaDict(
            type="OBJECT",
            properties=properties,
            required=required_params,
        ),
    )
    return function_declaration
