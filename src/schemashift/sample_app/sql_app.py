"""SQL (PostgreSQL) shop application stubs.

Placeholder that will use the generated ORM layer once the migration
pipeline produces one.  All methods raise ``NotImplementedError`` for now.

Spec: sample_app/sql-app
"""

from __future__ import annotations

from typing import Any


class SQLShopApp:
    """Stub CRUD wrapper for the migrated PostgreSQL *shop* schema.

    Parameters
    ----------
    dsn:
        PostgreSQL connection string.
    """

    def __init__(self, dsn: str = "") -> None:
        self._dsn = dsn

    # -- User stubs ------------------------------------------------------

    def create_user(self, user: dict[str, Any]) -> int:
        """Insert a user row and return its primary key."""
        raise NotImplementedError("SQL user creation pending ORM generation.")

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        """Return a single user by primary key, or ``None``."""
        raise NotImplementedError("SQL user lookup pending ORM generation.")

    def list_users(self, *, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        """Return a paginated list of users."""
        raise NotImplementedError("SQL user listing pending ORM generation.")

    def update_user(self, user_id: int, updates: dict[str, Any]) -> bool:
        """Update fields on a user row.  Returns ``True`` if matched."""
        raise NotImplementedError("SQL user update pending ORM generation.")

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by primary key.  Returns ``True`` if deleted."""
        raise NotImplementedError("SQL user deletion pending ORM generation.")

    # -- Order stubs -----------------------------------------------------

    def place_order(
        self,
        user_id: int,
        items: list[dict[str, Any]],
        shipping_address: dict[str, str],
        *,
        carrier: str = "UPS",
        coupon_code: str | None = None,
    ) -> int:
        """Create an order for *user_id* and return its primary key."""
        raise NotImplementedError("SQL order placement pending ORM generation.")
