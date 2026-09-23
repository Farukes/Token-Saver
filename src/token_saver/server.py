"""Token-Saver MCP Server.

Central FastMCP server that registers all token-saving tools.
Communicates with AI coding assistants via stdio (JSON-RPC 2.0).
"""

import sys

from fastmcp import FastMCP

from token_saver.tools.skeleton import register_skeleton_tools
from token_saver.tools.smart_reader import register_smart_reader_tools
from token_saver.tools.output_pruner import register_output_pruner_tools
from token_saver.tools.repo_map import register_repo_map_tools

# Create the MCP server instance
mcp = FastMCP(
    name="token-saver",
    version="0.1.0",
)

# Register all tool modules
register_skeleton_tools(mcp)
register_smart_reader_tools(mcp)
register_output_pruner_tools(mcp)
register_repo_map_tools(mcp)

# Ensure debug output goes to stderr, never stdout (MCP protocol requirement)
if not sys.stderr.isatty():
    import logging

    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
