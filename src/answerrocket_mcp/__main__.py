"""Main entry point for the AnswerRocket MCP server."""

import sys
from .server import create_server


def main():
    """Run the MCP server."""
    try:
        mcp = create_server()
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()