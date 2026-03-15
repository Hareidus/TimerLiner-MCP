"""Entry point for ``python -m mcp_server`` — stdio MCP server."""

import asyncio
import sys

# Force UTF-8 for stdio on Windows (MCP protocol requires UTF-8)
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from mcp.server.stdio import stdio_server
from mcp_server.server import server
from mcp_server.auth import auto_login


async def main():
    await auto_login()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
