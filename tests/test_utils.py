import unittest

from mcp_vertexai_search.utils import to_mcp_tool


class TestUtils(unittest.TestCase):
    def test_to_mcp_tool(self):
        tool = to_mcp_tool("test-tool", "test-description")
        self.assertEqual(tool.name, "test-tool")
        self.assertEqual(tool.description, "test-description")
