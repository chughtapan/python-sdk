"""Group base class for FastMCP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from mcp.types import Annotations, Icon


class Group(BaseModel):
    """A group that organizes MCP primitives."""

    name: str = Field(description="Programmatic name of the group")
    title: str | None = Field(default=None, description="Human-readable title")
    description: str | None = Field(default=None, description="Description of the group")
    icons: list[Icon] | None = Field(default=None, description="Optional list of icons")
    annotations: Annotations | None = Field(default=None, description="Optional annotations")
    meta: dict[str, Any] | None = Field(default=None, description="Metadata including group membership")
