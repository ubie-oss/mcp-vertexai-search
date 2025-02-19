import unittest

from src.mcp_vertexai_search.config import (
    Config,
    DataStoreConfig,
    GenerateContentConfig,
    MCPServerConfig,
    VertexAIModelConfig,
)


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        """Test that default Config values are set correctly."""
        config = Config(
            model=VertexAIModelConfig(model_name="test-model", location="test-location"),
        )
        self.assertIsInstance(config.server, MCPServerConfig)
        self.assertIsInstance(config.model, VertexAIModelConfig)
        self.assertEqual(config.data_stores, [])

    def test_custom_config(self):
        """Test that Config can be initialized with custom values."""
        custom_server = MCPServerConfig(name="test-server")
        custom_model = VertexAIModelConfig(
            model_name="test-model",
            location="test-location"
        )
        custom_data_store = DataStoreConfig(
            project_id="test-project",
            location="test-location",
            datastore_id="test-datastore",
            tool_name="test-tool",
        )

        config = Config(
            server=custom_server,
            model=custom_model,
            data_stores=[custom_data_store]
        )

        self.assertEqual(config.server.name, "test-server")
        self.assertEqual(config.model.model_name, "test-model")
        self.assertEqual(config.model.location, "test-location")
        self.assertEqual(len(config.data_stores), 1)
        self.assertEqual(config.data_stores[0].datastore_id, "test-datastore")

    def test_default_mcpserverconfig(self):
        """Test MCPServerConfig default values."""
        server_config = MCPServerConfig()
        self.assertEqual(server_config.name, "document-search")

    def test_custom_mcpserverconfig(self):
        """Test MCPServerConfig with custom values."""
        server_config = MCPServerConfig(name="custom-server")
        self.assertEqual(server_config.name, "custom-server")

    def test_default_vertexaimodelconfig(self):
        """Test VertexAIModelConfig default values."""
        model_config = VertexAIModelConfig(
            model_name="test-model",
            location="test-location"
        )
        self.assertIsInstance(model_config.generate_content_config, GenerateContentConfig)
        self.assertEqual(model_config.generate_content_config.temperature, 0.7)
        self.assertEqual(model_config.generate_content_config.top_p, 0.95)

    def test_custom_vertexaimodelconfig(self):
        """Test VertexAIModelConfig with custom values."""
        custom_gen_config = GenerateContentConfig(temperature=0.8, top_p=0.9)
        model_config = VertexAIModelConfig(
            model_name="custom-model",
            location="custom-location",
            project_id="custom-project",
            generate_content_config=custom_gen_config,
        )
        self.assertEqual(model_config.model_name, "custom-model")
        self.assertEqual(model_config.location, "custom-location")
        self.assertEqual(model_config.project_id, "custom-project")
        self.assertEqual(model_config.generate_content_config.temperature, 0.8)
        self.assertEqual(model_config.generate_content_config.top_p, 0.9)

    def test_default_generatecontentconfig(self):
        """Test GenerateContentConfig default values."""
        gen_config = GenerateContentConfig()
        self.assertEqual(gen_config.temperature, 0.7)
        self.assertEqual(gen_config.top_p, 0.95)

    def test_custom_generatecontentconfig(self):
        """Test GenerateContentConfig with custom values."""
        gen_config = GenerateContentConfig(temperature=0.6, top_p=0.8)
        self.assertEqual(gen_config.temperature, 0.6)
        self.assertEqual(gen_config.top_p, 0.8)

    def test_default_datastoreconfig(self):
        """Test DataStoreConfig default values."""
        datastore_config = DataStoreConfig(
            project_id="test-project",
            location="test-location",
            datastore_id="test-datastore",
            tool_name="test-tool",
        )
        self.assertEqual(datastore_config.description, "")
        self.assertEqual(datastore_config.tool_name, "test-tool")

    def test_custom_datastoreconfig(self):
        """Test DataStoreConfig with custom values."""
        datastore_config = DataStoreConfig(
            project_id="custom-project",
            location="custom-location",
            datastore_id="custom-datastore",
            description="custom-description",
            tool_name="custom-tool",
        )
        self.assertEqual(datastore_config.project_id, "custom-project")
        self.assertEqual(datastore_config.location, "custom-location")
        self.assertEqual(datastore_config.datastore_id, "custom-datastore")
        self.assertEqual(datastore_config.description, "custom-description")
        self.assertEqual(datastore_config.tool_name, "custom-tool")

    def test_computed_tool_name_datastoreconfig(self):
        """Test DataStoreConfig computed tool name when not provided."""
        datastore_config = DataStoreConfig(
            project_id="custom-project",
            location="custom-location",
            datastore_id="custom-datastore",
            description="custom-description",
            tool_name = "document-search"
        )
        expected_tool_name = "document-search"
        self.assertEqual(datastore_config.tool_name, expected_tool_name)
