"""Tests for groups functionality in the low-level server."""

import pytest

import mcp.types as types
from mcp.server.lowlevel.server import NotificationOptions, Server


class TestNotificationOptions:
    """Test NotificationOptions with groups_changed."""

    def test_groups_changed_default(self):
        """Test that groups_changed defaults to False."""
        options = NotificationOptions()
        assert options.groups_changed is False

    def test_groups_changed_true(self):
        """Test that groups_changed can be set to True."""
        options = NotificationOptions(groups_changed=True)
        assert options.groups_changed is True


class TestServerCapabilities:
    """Test server capabilities for groups."""

    def test_groups_capability_not_set_without_handler(self):
        """Test that groups capability is not set when no handler is registered."""
        server = Server("test")
        notification_options = NotificationOptions()
        capabilities = server.get_capabilities(notification_options, {})

        assert capabilities.groups is None

    def test_groups_capability_set_with_handler(self):
        """Test that groups capability is set when handler is registered."""
        server = Server("test")

        @server.list_groups()
        async def list_groups() -> list[types.Group]:
            return []

        notification_options = NotificationOptions()
        capabilities = server.get_capabilities(notification_options, {})

        assert capabilities.groups is not None
        assert capabilities.groups.list_changed is False

    def test_groups_capability_with_list_changed(self):
        """Test that groups capability includes list_changed flag."""
        server = Server("test")

        @server.list_groups()
        async def list_groups() -> list[types.Group]:
            return []

        notification_options = NotificationOptions(groups_changed=True)
        capabilities = server.get_capabilities(notification_options, {})

        assert capabilities.groups is not None
        assert capabilities.groups.list_changed is True


class TestListGroupsDecorator:
    """Test list_groups decorator functionality."""

    @pytest.mark.anyio
    async def test_list_groups_decorator_simple(self):
        """Test list_groups decorator with simple list return."""
        server = Server("test")

        @server.list_groups()
        async def list_groups() -> list[types.Group]:
            return [
                types.Group(name="g1", title="Group 1"),
                types.Group(name="g2", title="Group 2"),
            ]

        # Verify handler was registered
        assert types.ListGroupsRequest in server.request_handlers

    @pytest.mark.anyio
    async def test_list_groups_decorator_with_request(self):
        """Test list_groups decorator with ListGroupsRequest parameter."""
        server = Server("test")

        @server.list_groups()
        async def list_groups(request: types.ListGroupsRequest) -> types.ListGroupsResult:
            cursor = request.params.cursor if request.params else None
            return types.ListGroupsResult(groups=[types.Group(name="test", description=f"cursor={cursor}")])

        # Verify handler was registered
        assert types.ListGroupsRequest in server.request_handlers


class TestGroupTypes:
    """Test Group type functionality."""

    def test_group_creation(self):
        """Test creating a Group."""
        group = types.Group(
            name="test-group",
            title="Test Group",
            description="A test group",
        )

        assert group.name == "test-group"
        assert group.title == "Test Group"
        assert group.description == "A test group"

    def test_group_with_meta(self):
        """Test Group with _meta field."""
        from mcp import GROUPS_META_KEY

        group = types.Group(
            name="child",
            title="Child Group",
            _meta={GROUPS_META_KEY: ["parent"]},
        )

        assert group.meta is not None
        assert GROUPS_META_KEY in group.meta
        assert "parent" in group.meta[GROUPS_META_KEY]

    def test_group_with_icons(self):
        """Test Group with icons."""
        icons = [types.Icon(src="data:image/svg+xml,<svg></svg>")]
        group = types.Group(name="icon-group", icons=icons)

        assert group.icons is not None
        assert len(group.icons) == 1

    def test_group_with_annotations(self):
        """Test Group with annotations."""
        annotations = types.Annotations(audience=["user"])
        group = types.Group(name="annotated", annotations=annotations)

        assert group.annotations is not None
        assert group.annotations.audience == ["user"]


class TestGroupsMetaKey:
    """Test GROUPS_META_KEY constant."""

    def test_groups_meta_key_value(self):
        """Test GROUPS_META_KEY has correct value."""
        from mcp import GROUPS_META_KEY

        assert GROUPS_META_KEY == "io.modelcontextprotocol/groups"

    def test_groups_meta_key_is_final(self):
        """Test GROUPS_META_KEY is a string constant."""
        from mcp.types import GROUPS_META_KEY

        assert isinstance(GROUPS_META_KEY, str)


class TestGroupListChangedNotification:
    """Test GroupListChangedNotification type."""

    def test_notification_creation(self):
        """Test creating a GroupListChangedNotification."""
        notification = types.GroupListChangedNotification()

        assert notification.method == "notifications/groups/list_changed"
        assert notification.params is None

    def test_notification_in_server_notification_type(self):
        """Test GroupListChangedNotification is in ServerNotificationType."""
        notification = types.GroupListChangedNotification()
        server_notification = types.ServerNotification(notification)

        assert server_notification.root == notification
