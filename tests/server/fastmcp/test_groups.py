"""Tests for FastMCP groups functionality."""

import logging

import pytest

from mcp import GROUPS_META_KEY
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.groups import Group, GroupManager


class TestGroupManager:
    """Test GroupManager functionality."""

    def test_add_group(self):
        """Test adding a group."""
        manager = GroupManager()
        group = Group(name="test-group", title="Test Group", description="A test group")
        result = manager.add_group(group)

        assert result == group
        retrieved = manager.get_group("test-group")
        assert retrieved is not None
        assert retrieved.name == "test-group"

    def test_get_nonexistent_group(self):
        """Test getting a non-existent group returns None."""
        manager = GroupManager()
        assert manager.get_group("nonexistent") is None

    def test_list_groups(self):
        """Test listing all groups."""
        manager = GroupManager()
        group1 = Group(name="group1", title="Group 1")
        group2 = Group(name="group2", title="Group 2")

        manager.add_group(group1)
        manager.add_group(group2)

        groups = manager.list_groups()
        assert len(groups) == 2
        names = [g.name for g in groups]
        assert "group1" in names
        assert "group2" in names

    def test_remove_group(self):
        """Test removing a group."""
        manager = GroupManager()
        group = Group(name="to-remove", title="To Remove")
        manager.add_group(group)

        assert manager.get_group("to-remove") is not None
        manager.remove_group("to-remove")
        assert manager.get_group("to-remove") is None

    def test_remove_nonexistent_group(self):
        """Test removing a non-existent group does nothing."""
        manager = GroupManager()
        # Should not raise an exception
        manager.remove_group("nonexistent")

    def test_warn_on_duplicate_groups(self, caplog: pytest.LogCaptureFixture):
        """Test warning on duplicate group registration."""
        manager = GroupManager(warn_on_duplicate_groups=True)
        group = Group(name="dup", title="Duplicate")

        manager.add_group(group)
        with caplog.at_level(logging.WARNING):
            manager.add_group(group)
            assert "Group 'dup' is already registered" in caplog.text

    def test_disable_warn_on_duplicate_groups(self, caplog: pytest.LogCaptureFixture):
        """Test disabling warning on duplicate groups."""
        manager = GroupManager(warn_on_duplicate_groups=False)
        group = Group(name="dup", title="Duplicate")

        manager.add_group(group)
        with caplog.at_level(logging.WARNING):
            manager.add_group(group)
            assert "Group 'dup' is already registered" not in caplog.text

    def test_group_with_nested_groups_via_meta(self):
        """Test creating a group with nested group membership via _meta."""
        manager = GroupManager()

        # Create parent group
        parent = Group(name="parent", title="Parent Group")
        manager.add_group(parent)

        # Create child group with parent membership via meta
        child = Group(name="child", title="Child Group", meta={GROUPS_META_KEY: ["parent"]})
        manager.add_group(child)

        # Verify the meta is preserved
        retrieved_child = manager.get_group("child")
        assert retrieved_child is not None
        assert retrieved_child.meta is not None
        assert GROUPS_META_KEY in retrieved_child.meta
        assert "parent" in retrieved_child.meta[GROUPS_META_KEY]


class TestFastMCPGroups:
    """Test FastMCP groups integration."""

    def test_add_group_via_fastmcp(self):
        """Test adding a group via FastMCP."""
        mcp = FastMCP("test")

        group = mcp.add_group("test-group", title="Test Group", description="A test group for testing")

        assert group.name == "test-group"
        assert group.title == "Test Group"
        assert group.description == "A test group for testing"

    @pytest.mark.anyio
    async def test_list_groups(self):
        """Test listing groups via FastMCP."""
        mcp = FastMCP("test")

        mcp.add_group("group1", title="Group 1")
        mcp.add_group("group2", title="Group 2", description="Second group")

        groups = await mcp.list_groups()
        assert len(groups) == 2

        names = [g.name for g in groups]
        assert "group1" in names
        assert "group2" in names

    def test_remove_group_via_fastmcp(self):
        """Test removing a group via FastMCP."""
        mcp = FastMCP("test")
        mcp.add_group("to-remove", title="To Remove")

        # Verify it exists
        assert mcp._group_manager.get_group("to-remove") is not None

        mcp.remove_group("to-remove")

        # Verify it's removed
        assert mcp._group_manager.get_group("to-remove") is None

    @pytest.mark.anyio
    async def test_group_with_icons(self):
        """Test creating a group with icons."""
        from mcp.types import Icon

        mcp = FastMCP("test")

        icons = [Icon(src="data:image/svg+xml,<svg></svg>")]
        mcp.add_group("icons-group", title="Icons Group", icons=icons)

        groups = await mcp.list_groups()
        assert len(groups) == 1
        assert groups[0].icons is not None
        assert len(groups[0].icons) == 1

    @pytest.mark.anyio
    async def test_group_with_annotations(self):
        """Test creating a group with annotations."""
        from mcp.types import Annotations

        mcp = FastMCP("test")

        annotations = Annotations(audience=["user"])
        mcp.add_group("annotated-group", title="Annotated Group", annotations=annotations)

        groups = await mcp.list_groups()
        assert len(groups) == 1
        assert groups[0].annotations is not None
        assert groups[0].annotations.audience == ["user"]

    @pytest.mark.anyio
    async def test_nested_groups_via_meta(self):
        """Test creating nested groups via _meta."""
        mcp = FastMCP("test")

        # Create parent group
        mcp.add_group("communications", title="Communications", description="Communication tools")

        # Create child group with parent membership
        mcp.add_group(
            "email",
            title="Email",
            description="Email operations",
            meta={GROUPS_META_KEY: ["communications"]},
        )

        groups = await mcp.list_groups()
        assert len(groups) == 2

        # Find email group and verify meta
        email_group = next(g for g in groups if g.name == "email")
        assert email_group.meta is not None
        assert GROUPS_META_KEY in email_group.meta
        assert "communications" in email_group.meta[GROUPS_META_KEY]

    @pytest.mark.anyio
    async def test_tool_with_group_membership(self):
        """Test that tools can have group membership via _meta."""
        mcp = FastMCP("test")

        # Create a group
        mcp.add_group("email", title="Email")

        # Create a tool with group membership
        @mcp.tool(meta={GROUPS_META_KEY: ["email"]})
        def send_email(to: str, subject: str) -> str:  # pragma: no cover
            """Send an email."""
            return f"Sent to {to}"

        tools = await mcp.list_tools()
        assert len(tools) == 1
        assert tools[0].meta is not None
        assert GROUPS_META_KEY in tools[0].meta
        assert "email" in tools[0].meta[GROUPS_META_KEY]

    def test_warn_on_duplicate_groups_setting(self, caplog: pytest.LogCaptureFixture):
        """Test warn_on_duplicate_groups setting."""
        mcp = FastMCP("test", warn_on_duplicate_groups=True)

        mcp.add_group("dup", title="Duplicate")
        with caplog.at_level(logging.WARNING):
            mcp.add_group("dup", title="Duplicate")
            assert "Group 'dup' is already registered" in caplog.text

    def test_disable_warn_on_duplicate_groups_setting(self, caplog: pytest.LogCaptureFixture):
        """Test disabling warn_on_duplicate_groups setting."""
        mcp = FastMCP("test", warn_on_duplicate_groups=False)

        mcp.add_group("dup", title="Duplicate")
        with caplog.at_level(logging.WARNING):
            mcp.add_group("dup", title="Duplicate")
            assert "Group 'dup' is already registered" not in caplog.text
