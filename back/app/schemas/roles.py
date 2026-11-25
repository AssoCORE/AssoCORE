"""Schemas for role assignment (R1).

The first per-domain schema module: new features add their own file here rather
than growing `classes.py`.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.classes import BaseSchema, RoleOut


class RolesUpdate(BaseSchema):
    """The full set of roles the user should hold. `member` is always kept."""

    roles: list[str] = Field(default_factory=list, max_length=32)


class RoleChangeOut(BaseSchema):
    id: int
    role: RoleOut
    action: Literal["grant", "revoke"]
    # Null when the change was made by the system or by a since-deleted account.
    changed_by: int | None
    created_at: datetime
