"""Entry point for the ``khaya-mcp`` console script."""

import sys


def main() -> None:
    try:
        from khaya.mcp.server import MissingAPIKeyError, build_server
    except ModuleNotFoundError as e:  # pragma: no cover - depends on install shape
        if e.name != "mcp":
            raise
        sys.exit("The MCP server needs the 'mcp' extra:\n\n    pip install khaya[mcp]\n")

    try:
        server = build_server()
    except MissingAPIKeyError as e:
        sys.exit(str(e))

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
