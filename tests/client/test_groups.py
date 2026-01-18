"""Tests for groups/list client/server integration."""

import pytest

import mcp.types as types
from mcp import GROUPS_META_KEY, Client
from mcp.server import Server
from mcp.server.fastmcp import FastMCP

pytestmark = pytest.mark.anyio


async def test_list_groups_with_fastmcp():
    """Test listing groups from a FastMCP server."""
    server = FastMCP("test")
    server.add_group("group1", title="Group 1", description="First group")
    server.add_group("group2", title="Group 2", description="Second group")

    async with Client(server) as client:
        result = await client.list_groups()

        assert isinstance(result, types.ListGroupsResult)
        assert len(result.groups) == 2

        names = [g.name for g in result.groups]
        assert "group1" in names
        assert "group2" in names


async def test_list_groups_empty():
    """Test listing groups when no groups are registered."""
    server = FastMCP("test")

    async with Client(server) as client:
        result = await client.list_groups()

        assert isinstance(result, types.ListGroupsResult)
        assert len(result.groups) == 0


async def test_list_groups_with_nested_groups():
    """Test listing groups with nested group membership."""
    server = FastMCP("test")
    server.add_group("parent", title="Parent")
    server.add_group("child", title="Child", meta={GROUPS_META_KEY: ["parent"]})

    async with Client(server) as client:
        result = await client.list_groups()

        assert len(result.groups) == 2

        child_group = next(g for g in result.groups if g.name == "child")
        assert child_group.meta is not None
        assert GROUPS_META_KEY in child_group.meta
        assert "parent" in child_group.meta[GROUPS_META_KEY]


async def test_list_groups_with_lowlevel_server():
    """Test that list_groups works with a lowlevel Server."""
    server = Server("test-lowlevel")

    @server.list_groups()
    async def handle_list_groups(request: types.ListGroupsRequest) -> types.ListGroupsResult:
        # Echo back what cursor we received in the group description
        cursor = request.params.cursor if request.params else None
        return types.ListGroupsResult(
            groups=[
                types.Group(
                    name="test_group",
                    description=f"cursor={cursor}",
                )
            ]
        )

    async with Client(server) as client:
        result = await client.list_groups(params=types.PaginatedRequestParams())
        assert result.groups[0].description == "cursor=None"

        result = await client.list_groups(params=types.PaginatedRequestParams(cursor="page2"))
        assert result.groups[0].description == "cursor=page2"


async def test_list_groups_returns_list_style():
    """Test that list_groups works when handler returns list[Group]."""
    server = Server("test-lowlevel")

    @server.list_groups()
    async def handle_list_groups() -> list[types.Group]:
        return [
            types.Group(name="simple1", title="Simple 1"),
            types.Group(name="simple2", title="Simple 2"),
        ]

    async with Client(server) as client:
        result = await client.list_groups()
        assert len(result.groups) == 2


async def test_groups_capability_advertised():
    """Test that groups capability is advertised when groups handler is registered."""
    server = FastMCP("test")
    server.add_group("test", title="Test Group")

    async with Client(server) as client:
        capabilities = client.get_server_capabilities()

        assert capabilities is not None
        assert capabilities.groups is not None


async def test_groups_with_icons_and_annotations():
    """Test listing groups with icons and annotations."""
    server = FastMCP("test")
    server.add_group(
        "styled-group",
        title="Styled Group",
        description="A group with styling",
        icons=[types.Icon(src="data:image/svg+xml,<svg>test</svg>")],
        annotations=types.Annotations(audience=["user", "assistant"]),
    )

    async with Client(server) as client:
        result = await client.list_groups()

        assert len(result.groups) == 1
        group = result.groups[0]
        assert group.name == "styled-group"
        assert group.icons is not None
        assert len(group.icons) == 1
        assert group.annotations is not None
        assert group.annotations.audience == ["user", "assistant"]
