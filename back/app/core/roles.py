"""Role names.

Kept in `core` so nothing has to import ORM models just to name a role.
"""

ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_MEMBER = "member"

DEFAULT_ROLES = (ROLE_ADMIN, ROLE_STAFF, ROLE_MEMBER)
