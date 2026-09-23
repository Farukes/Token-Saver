"""Entry point for running Token-Saver as a module: python -m token_saver"""

from token_saver.server import mcp


def main():
    """Run the Token-Saver MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
