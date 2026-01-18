"""Group manager for FastMCP."""

from __future__ import annotations

import logging

from mcp.server.fastmcp.groups.base import Group

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages groups for FastMCP server."""

    def __init__(self, warn_on_duplicate_groups: bool = True) -> None:
        self._groups: dict[str, Group] = {}
        self._warn_on_duplicate_groups = warn_on_duplicate_groups

    def add_group(self, group: Group) -> Group:
        """Add a group to the manager.

        Args:
            group: The group to add

        Returns:
            The added group, or the existing group if already registered
        """
        existing = self._groups.get(group.name)
        if existing:
            if self._warn_on_duplicate_groups:
                logger.warning(f"Group '{group.name}' is already registered")
            return existing
        self._groups[group.name] = group
        return group

    def get_group(self, name: str) -> Group | None:
        """Get a group by name.

        Args:
            name: The name of the group

        Returns:
            The group if found, None otherwise
        """
        return self._groups.get(name)

    def remove_group(self, name: str) -> None:
        """Remove a group by name.

        Args:
            name: The name of the group to remove
        """
        if name in self._groups:
            del self._groups[name]

    def list_groups(self) -> list[Group]:
        """List all registered groups.

        Returns:
            List of all groups
        """
        return list(self._groups.values())
