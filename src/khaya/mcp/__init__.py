"""MCP server exposing the Khaya API as tools for AI clients.

Requires the ``mcp`` extra::

    pip install khaya[mcp]

Never imported by ``khaya/__init__.py`` — the core install stays free of the
dependency.
"""

from typing import Any

__all__ = ["build_server"]


def __getattr__(name: str) -> Any:
    """Import the server lazily.

    Importing it eagerly would raise ModuleNotFoundError from this package's
    __init__, before ``__main__.main`` could catch it and print the install
    hint — which is exactly what the console script needs to do.
    """
    if name == "build_server":
        from khaya.mcp.server import build_server

        return build_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
