import pytest
from pydantic import FileUrl

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import (
    create_connected_server_and_client_session as create_session,
)


@pytest.mark.anyio
async def test_set_roots():
    server = FastMCP("test")

    @server.tool("check_roots")
    async def check_roots():
        return f"Server has {len(server.roots)} roots"

    async with create_session(server._mcp_server) as client_session:
        roots_to_set = [
            types.Root(
                uri=FileUrl("file:///users/fake/test"),
                name="Test Root 1",
            ),
            types.Root(
                uri=FileUrl("file:///users/fake/test/2"),
                name="Test Root 2",
            ),
        ]

        result = await client_session.set_roots(roots_to_set)
        assert isinstance(result, types.EmptyResult)

        tool_result = await client_session.call_tool("check_roots", {})
        assert tool_result.isError is False
        assert len(tool_result.content) > 0
        content = tool_result.content[0]
        assert isinstance(content, types.TextContent)
        assert content.text == "Server has 2 roots"


@pytest.mark.anyio
async def test_list_roots():
    server = FastMCP("test")

    async with create_session(server._mcp_server) as client_session:
        # Initially no roots
        result = await client_session.list_roots()
        assert result.roots == []

        # Set some roots
        roots_to_set = [
            types.Root(uri=FileUrl("file:///project/src"), name="Source"),
            types.Root(uri=FileUrl("file:///project/tests"), name="Tests"),
        ]
        await client_session.set_roots(roots_to_set)

        # Query them back
        result = await client_session.list_roots()
        assert len(result.roots) == 2
        assert result.roots[0].name == "Source"
        assert result.roots[1].name == "Tests"


@pytest.mark.anyio
async def test_roots_replacement():
    server = FastMCP("test")

    @server.tool("get_root_names")
    async def get_root_names():
        if not server.roots:
            return "No roots"
        return ", ".join(r.name or str(r.uri) for r in server.roots)

    async with create_session(server._mcp_server) as client_session:
        # Set initial roots
        initial_roots = [
            types.Root(uri=FileUrl("file:///project/src"), name="Source Code"),
            types.Root(uri=FileUrl("file:///project/tests"), name="Tests"),
            types.Root(uri=FileUrl("file:///project/docs"), name="Documentation"),
        ]
        await client_session.set_roots(initial_roots)

        result = await client_session.call_tool("get_root_names", {})
        content = result.content[0]
        assert isinstance(content, types.TextContent)
        assert "Source Code" in content.text
        assert "Tests" in content.text
        assert "Documentation" in content.text

        # Replace with new roots
        new_roots = [types.Root(uri=FileUrl("file:///new/location"), name="New Location")]
        await client_session.set_roots(new_roots)

        result = await client_session.call_tool("get_root_names", {})
        content = result.content[0]
        assert isinstance(content, types.TextContent)
        assert content.text == "New Location"

        # Clear roots
        await client_session.set_roots([])

        result = await client_session.call_tool("get_root_names", {})
        content = result.content[0]
        assert isinstance(content, types.TextContent)
        assert content.text == "No roots"
