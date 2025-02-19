from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class GenerateContentConfig(BaseModel):
    """The configuration for the generate content API."""

    temperature: float = Field(
        description="The temperature for the generate content API",
        default=0.7,
    )
    top_p: float = Field(
        description="The top p for the generate content API",
        default=0.95,
    )


class VertexAIModelConfig(BaseModel):
    """The configuration for a Vertex AI model."""

    model_name: str = Field(..., description="The name of the Vertex AI model")
    project_id: Optional[str] = Field(
        None, description="The project ID of the Vertex AI model"
    )
    location: str = Field(..., description="The location of the model")
    generate_content_config: Optional[GenerateContentConfig] = Field(
        description="The configuration for the generate content API",
        default_factory=GenerateContentConfig,
    )


class DataStoreConfig(BaseModel):
    """The configuration for a Vertex AI data store."""

    project_id: str = Field(
        ..., description="The project ID of the Vertex AI data store"
    )
    location: str = Field(..., description="The location of the Vertex AI data store")
    datastore_id: str = Field(..., description="The ID of the Vertex AI data store")
    tool_name: str = Field(
        ...,
        description="The name of the tool. If not provided, defaults to 'search_document_<datastore_id>'",
    )
    description: str = Field(
        description="The description of the Vertex AI data store",
        default="",
    )


class MCPServerConfig(BaseModel):
    """The configuration for an MCP server."""

    name: str = Field(
        description="The name of the MCP server", default="document-search"
    )


class Config(BaseModel):
    """The configuration for the application."""

    server: MCPServerConfig = Field(
        description="The server configuration", default_factory=MCPServerConfig
    )
    model: VertexAIModelConfig = Field(
        description="The model configuration", default_factory=VertexAIModelConfig
    )
    data_stores: List[DataStoreConfig] = Field(
        description="The data stores configuration", default_factory=list
    )


def load_yaml_config(file_path: str) -> Config:
    """Load a YAML config file"""
    with open(file_path, "r") as f:
        return Config(**yaml.safe_load(f))
