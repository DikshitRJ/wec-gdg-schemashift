"""Simple pymongo CRUD interface against the *shop* database.

Provides create / get / list / update / delete for users, and a
``place_order`` helper.

Spec: sample_app/mongo-app
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import Decimal128, ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from schemashift.errors import SchemaShiftError


class MongoShopApp:
    """Thin CRUD wrapper around the *shop* MongoDB database.

    Parameters
    ----------
    client:
        A connected ``pymongo.MongoClient``.
    db_name:
        Name of the database (default ``"shop"``).
    """

    def __init__(self, client: MongoClient, *, db_name: str = "shop") -> None:
        self._client = client
        self._db: Database = client[db_name]

    # -- convenience accessors -------------------------------------------

    @property
    def users(self) -> Collection:
        """Return the *users* collection handle."""
        return self._db["users"]

    @property
    def products(self) -> Collection:
        """Return the *products* collection handle."""
        return self._db["products"]

    @property
    def orders(self) -> Collection:
        """Return the *orders* collection handle."""
        return self._db["orders"]

    @property
    def reviews(self) -> Collection:
        """Return the *reviews* collection handle."""
        return self._db["reviews"]

    # -- User CRUD -------------------------------------------------------

    def create_user(self, user: dict[str, Any]) -> ObjectId:
        """Insert a user document and return its ``_id``.

        Raises :class:`SchemaShiftError` if the email already exists.
        """
        required = {"name", "email"}
        missing = required - set(user)
        if missing:
            raise SchemaShiftError(
                f"Missing required user fields: {', '.join(sorted(missing))}",
                hint="Provide at least 'name' and 'email'.",
            )
        doc = {
            **user,
            "createdAt": user.get("createdAt", datetime.now(tz=timezone.utc)),
        }
        try:
            result = self.users.insert_one(doc)
        except Exception as exc:
            raise SchemaShiftError(
                f"Failed to create user: {exc}",
                hint="Check for duplicate email or connectivity issues.",
            ) from exc
        return result.inserted_id

    def get_user(self, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a single user by ``_id``, or ``None``."""
        return self.users.find_one({"_id": user_id})

    def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return a paginated list of users sorted by email."""
        return list(
            self.users.find().sort("email", 1).skip(skip).limit(limit)
        )

    def update_user(self, user_id: ObjectId, updates: dict[str, Any]) -> bool:
        """Update fields on a user document.  Returns ``True`` if matched."""
        result = self.users.update_one({"_id": user_id}, {"$set": updates})
        return result.matched_count > 0

    def delete_user(self, user_id: ObjectId) -> bool:
        """Delete a user by ``_id``.  Returns ``True`` if deleted."""
        result = self.users.delete_one({"_id": user_id})
        return result.deleted_count > 0

    # -- Order helpers ---------------------------------------------------

    def place_order(
        self,
        user_id: ObjectId,
        items: list[dict[str, Any]],
        shipping_address: dict[str, str],
        *,
        carrier: str = "UPS",
        coupon_code: str | None = None,
    ) -> ObjectId:
        """Create an order document for *user_id*.

        Parameters
        ----------
        user_id:
            Must reference an existing user.
        items:
            List of ``{"sku": str, "qty": int}``.  ``unitPrice`` is
            looked up from the *products* collection.
        shipping_address:
            ``{"street", "city", "state", "zip"}`` mapping.
        carrier:
            Shipping carrier name.
        coupon_code:
            Optional coupon code string.

        Returns
        -------
        ObjectId
            The ``_id`` of the inserted order.
        """
        # Validate user exists
        if self.users.count_documents({"_id": user_id}, limit=1) == 0:
            raise SchemaShiftError(
                f"User {user_id} does not exist.",
                hint="Pass a valid user ObjectId.",
            )

        enriched_items: list[dict[str, Any]] = []
        for item in items:
            product = self.products.find_one({"sku": item["sku"]})
            if product is None:
                raise SchemaShiftError(
                    f"Product with SKU '{item['sku']}' not found.",
                    hint="Ensure the product exists before ordering.",
                )
            enriched_items.append({
                "sku": item["sku"],
                "qty": item["qty"],
                "unitPrice": product["price"],
            })

        order: dict[str, Any] = {
            "userId": user_id,
            "status": "pending",
            "shipping": {
                "carrier": carrier,
                "trackingNo": "",
                "address": shipping_address,
            },
            "items": enriched_items,
            "createdAt": datetime.now(tz=timezone.utc),
        }
        if coupon_code is not None:
            order["couponCode"] = coupon_code

        result = self.orders.insert_one(order)
        return result.inserted_id
