"""Deterministic shop-database seed data generator.

Generates users, products, orders, and reviews for a MongoDB *shop*
database using ``random.Random(42)`` so that every invocation produces
byte-identical data.

Spec: seed/shop
"""

from __future__ import annotations

import random
import string
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from bson import Decimal128, ObjectId

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SEED = 42

_FIRST_NAMES: list[str] = [
    "Alice",
    "Bob",
    "Carol",
    "Dave",
    "Eve",
    "Frank",
    "Grace",
    "Heidi",
    "Ivan",
    "Judy",
    "Karl",
    "Laura",
    "Mallory",
    "Niaj",
    "Oscar",
    "Peggy",
    "Quentin",
    "Rupert",
    "Sybil",
    "Trent",
    "Uma",
    "Victor",
    "Wendy",
    "Xander",
    "Yuki",
    "Zara",
]

_LAST_NAMES: list[str] = [
    "Adams",
    "Baker",
    "Clark",
    "Diaz",
    "Evans",
    "Foster",
    "Garcia",
    "Harris",
    "Ito",
    "Johnson",
    "Kim",
    "Lee",
    "Martinez",
    "Nguyen",
    "Olson",
    "Patel",
    "Quinn",
    "Rivera",
    "Smith",
    "Taylor",
    "Ueda",
    "Vargas",
    "Williams",
    "Xu",
    "Young",
    "Zhang",
]

_STREETS: list[str] = [
    "Main St",
    "Oak Ave",
    "Pine Rd",
    "Elm Blvd",
    "Maple Dr",
    "Cedar Ln",
    "Birch Way",
    "Walnut Ct",
    "Spruce Pl",
    "Ash Cir",
]

_CITIES: list[str] = [
    "Springfield",
    "Riverdale",
    "Fairview",
    "Madison",
    "Georgetown",
    "Clinton",
    "Arlington",
    "Salem",
    "Chester",
    "Greenville",
]

_STATES: list[str] = [
    "CA",
    "TX",
    "NY",
    "FL",
    "IL",
    "PA",
    "OH",
    "GA",
    "NC",
    "MI",
    "NJ",
    "VA",
    "WA",
    "AZ",
    "MA",
    "TN",
    "IN",
    "MO",
    "MD",
    "WI",
]

_PRODUCT_ADJECTIVES: list[str] = [
    "Premium",
    "Classic",
    "Eco",
    "Ultra",
    "Pro",
    "Mini",
    "Mega",
    "Smart",
    "Turbo",
    "Deluxe",
]

_PRODUCT_NOUNS: list[str] = [
    "Widget",
    "Gadget",
    "Gizmo",
    "Doohickey",
    "Thingamajig",
    "Sprocket",
    "Contraption",
    "Device",
    "Module",
    "Apparatus",
]

_CATEGORIES: list[str] = [
    "electronics",
    "home",
    "garden",
    "sports",
    "books",
    "toys",
    "clothing",
    "health",
    "automotive",
    "food",
]

_ATTR_KEYS: list[str] = [
    "color",
    "weight_kg",
    "material",
    "warranty_months",
    "brand",
    "origin",
    "voltage",
    "dimensions",
]

_CARRIERS: list[str] = ["UPS", "FedEx", "USPS", "DHL"]
_ORDER_STATUSES: list[str] = ["pending", "shipped", "delivered", "cancelled"]

_TAGS: list[str] = [
    "vip",
    "wholesale",
    "returning",
    "new",
    "beta-tester",
    "influencer",
    "enterprise",
    "early-adopter",
]

_THEMES: list[str] = ["light", "dark", "system"]

_REVIEW_TITLES: list[str] = [
    "Great product!",
    "Not bad",
    "Could be better",
    "Love it",
    "Terrible quality",
    "Exceeded expectations",
    "Decent value",
    "Would buy again",
    "Disappointing",
    "Perfect for me",
]

_UNCOERCIBLE_RATINGS: list[str] = [
    "great",
    "terrible",
    "amazing",
    "awful",
    "okay",
    "fantastic",
    "mediocre",
    "superb",
    "poor",
    "excellent",
]

_COUPON_CODES: list[str] = [
    "SAVE10",
    "WELCOME",
    "SUMMER20",
    "VIP15",
    "FLASH25",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rng() -> random.Random:
    """Return a fresh deterministic RNG."""
    return random.Random(_SEED)


def _make_oid(rng: random.Random) -> ObjectId:
    """Generate a deterministic ObjectId from random bytes."""
    raw = bytes(rng.randint(0, 255) for _ in range(12))
    return ObjectId(raw)


def _make_email(first: str, last: str, idx: int) -> str:
    """Build a unique email address."""
    return f"{first.lower()}.{last.lower()}{idx}@example.com"


def _make_sku(idx: int) -> str:
    """Build a deterministic SKU."""
    return f"SKU-{idx:04d}"


def _rand_date(rng: random.Random, year: int = 2024) -> datetime:
    """Return a deterministic datetime in the given year."""
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)  # safe for all months
    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _rand_decimal(rng: random.Random, lo: float, hi: float, places: int = 2) -> Decimal128:
    """Return a deterministic Decimal128 value."""
    val = round(rng.uniform(lo, hi), places)
    return Decimal128(Decimal(str(val)))


def _rand_address(rng: random.Random) -> dict[str, Any]:
    """Build a randomised address sub-document."""
    return {
        "street": f"{rng.randint(1, 9999)} {rng.choice(_STREETS)}",
        "city": rng.choice(_CITIES),
        "state": rng.choice(_STATES),
        "zip": f"{rng.randint(10000, 99999)}",
    }


def _rand_geo(rng: random.Random) -> dict[str, float]:
    """Build a randomised geo sub-document."""
    return {
        "lat": round(rng.uniform(25.0, 48.0), 6),
        "lng": round(rng.uniform(-125.0, -70.0), 6),
    }


def _tracking_number(rng: random.Random) -> str:
    """Generate a pseudo tracking number."""
    chars = string.ascii_uppercase + string.digits
    return "".join(rng.choice(chars) for _ in range(12))


# ---------------------------------------------------------------------------
# Collection builders
# ---------------------------------------------------------------------------


def _build_users(rng: random.Random, count: int = 200) -> list[dict[str, Any]]:
    """Generate *count* user documents."""
    users: list[dict[str, Any]] = []
    for i in range(count):
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        addr = _rand_address(rng)
        addr["geo"] = _rand_geo(rng)
        user: dict[str, Any] = {
            "_id": _make_oid(rng),
            "name": f"{first} {last}",
            "email": _make_email(first, last, i),
            "address": addr,
            "prefs": {
                "newsletter": rng.choice([True, False]),
                "theme": rng.choice(_THEMES),
            },
            "tags": sorted(rng.sample(_TAGS, k=rng.randint(0, 3))),
            "createdAt": _rand_date(rng),
        }
        users.append(user)
    return users


def _build_products(rng: random.Random, count: int = 50) -> list[dict[str, Any]]:
    """Generate *count* product documents with varying attrs."""
    products: list[dict[str, Any]] = []
    for i in range(count):
        adj = rng.choice(_PRODUCT_ADJECTIVES)
        noun = rng.choice(_PRODUCT_NOUNS)
        # Build free-form attrs with varying keys per document
        num_attrs = rng.randint(1, len(_ATTR_KEYS))
        attr_keys = rng.sample(_ATTR_KEYS, k=num_attrs)
        attrs: dict[str, str] = {}
        for key in sorted(attr_keys):
            if key == "color":
                attrs[key] = rng.choice(["red", "blue", "green", "black", "white"])
            elif key == "weight_kg":
                attrs[key] = str(round(rng.uniform(0.1, 25.0), 1))
            elif key == "material":
                attrs[key] = rng.choice(["plastic", "metal", "wood", "glass", "fabric"])
            elif key == "warranty_months":
                attrs[key] = str(rng.choice([6, 12, 24, 36]))
            elif key == "brand":
                attrs[key] = rng.choice(["AcmeCo", "Widgetron", "GizmoCorp", "TechPro"])
            elif key == "origin":
                attrs[key] = rng.choice(["USA", "China", "Germany", "Japan", "Mexico"])
            elif key == "voltage":
                attrs[key] = rng.choice(["110V", "220V", "12V", "5V"])
            else:  # dimensions
                w = rng.randint(1, 100)
                h = rng.randint(1, 100)
                d = rng.randint(1, 100)
                attrs[key] = f"{w}x{h}x{d}cm"

        product: dict[str, Any] = {
            "_id": _make_oid(rng),
            "name": f"{adj} {noun} {i + 1}",
            "sku": _make_sku(i),
            "price": _rand_decimal(rng, 1.99, 999.99),
            "description": f"A {adj.lower()} {noun.lower()} for everyday use.",
            "categories": sorted(rng.sample(_CATEGORIES, k=rng.randint(1, 3))),
            "attrs": attrs,
            "inStock": rng.choice([True, True, True, False]),  # 75 % in stock
        }
        products.append(product)
    return products


def _build_orders(
    rng: random.Random,
    user_ids: list[ObjectId],
    skus: list[str],
    products_by_sku: dict[str, dict[str, Any]],
    count: int = 500,
) -> list[dict[str, Any]]:
    """Generate *count* order documents referencing existing users/products."""
    orders: list[dict[str, Any]] = []
    for _ in range(count):
        num_items = rng.randint(1, 5)
        chosen_skus = rng.choices(skus, k=num_items)
        items: list[dict[str, Any]] = []
        for sku in chosen_skus:
            prod = products_by_sku[sku]
            items.append(
                {
                    "sku": sku,
                    "qty": rng.randint(1, 10),
                    "unitPrice": prod["price"],
                }
            )

        order: dict[str, Any] = {
            "_id": _make_oid(rng),
            "userId": rng.choice(user_ids),
            "status": rng.choice(_ORDER_STATUSES),
            "shipping": {
                "carrier": rng.choice(_CARRIERS),
                "trackingNo": _tracking_number(rng),
                "address": _rand_address(rng),
            },
            "items": items,
            "createdAt": _rand_date(rng),
        }

        # ~20 % of orders have a coupon code
        if rng.random() < 0.20:
            order["couponCode"] = rng.choice(_COUPON_CODES)

        orders.append(order)
    return orders


def _build_reviews(
    rng: random.Random,
    user_ids: list[ObjectId],
    skus: list[str],
    count: int = 300,
) -> list[dict[str, Any]]:
    """Generate *count* review documents with ~15 % messy ratings."""
    reviews: list[dict[str, Any]] = []
    for _ in range(count):
        # ~15 % of ratings are string representations
        if rng.random() < 0.15:
            # Numeric-string rating like "5" or "3"
            rating: int | str = str(rng.randint(1, 5))
        else:
            rating = rng.randint(1, 5)

        review: dict[str, Any] = {
            "_id": _make_oid(rng),
            "productSku": rng.choice(skus),
            "userId": rng.choice(user_ids),
            "rating": rating,
            "title": rng.choice(_REVIEW_TITLES),
            "body": f"Review body text #{rng.randint(1, 10000)}.",
            "createdAt": _rand_date(rng),
        }
        reviews.append(review)
    return reviews


# ---------------------------------------------------------------------------
# Injection helpers
# ---------------------------------------------------------------------------


def _inject_orphan_review(
    rng: random.Random,
    reviews: list[dict[str, Any]],
    skus: list[str],
) -> None:
    """Append a review whose userId does not match any real user."""
    fake_user_id = _make_oid(rng)
    reviews.append(
        {
            "_id": _make_oid(rng),
            "productSku": rng.choice(skus),
            "userId": fake_user_id,
            "rating": 3,
            "title": "Orphan review — no matching user",
            "body": "This review references a userId that does not exist.",
            "createdAt": _rand_date(rng),
        }
    )


def _inject_bad_date(
    rng: random.Random,
    orders: list[dict[str, Any]],
    user_ids: list[ObjectId],
    skus: list[str],
    products_by_sku: dict[str, dict[str, Any]],
) -> None:
    """Append an order with createdAt set to a non-date string."""
    sku = rng.choice(skus)
    orders.append(
        {
            "_id": _make_oid(rng),
            "userId": rng.choice(user_ids),
            "status": "pending",
            "shipping": {
                "carrier": "UPS",
                "trackingNo": _tracking_number(rng),
                "address": _rand_address(rng),
            },
            "items": [{"sku": sku, "qty": 1, "unitPrice": products_by_sku[sku]["price"]}],
            "createdAt": "not-a-date",
        }
    )


def _inject_uncoercible_rating(
    rng: random.Random,
    reviews: list[dict[str, Any]],
    user_ids: list[ObjectId],
    skus: list[str],
) -> None:
    """Append reviews with word-based ratings that cannot be cast to int."""
    for word in _UNCOERCIBLE_RATINGS[:3]:
        reviews.append(
            {
                "_id": _make_oid(rng),
                "productSku": rng.choice(skus),
                "userId": rng.choice(user_ids),
                "rating": word,
                "title": f"Uncoercible rating: {word}",
                "body": f"This review has a non-numeric rating string: {word}.",
                "createdAt": _rand_date(rng),
            }
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_shop_data(
    *,
    inject: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Generate deterministic shop dataset documents in memory.

    Returns mapping of collection name -> list of document dicts.
    """
    inject = inject or set()
    rng = _rng()

    users = _build_users(rng, count=200)
    products = _build_products(rng, count=50)

    user_ids: list[ObjectId] = [u["_id"] for u in users]
    skus: list[str] = [p["sku"] for p in products]
    products_by_sku: dict[str, dict[str, Any]] = {p["sku"]: p for p in products}

    orders = _build_orders(rng, user_ids, skus, products_by_sku, count=500)
    reviews = _build_reviews(rng, user_ids, skus, count=300)

    if "orphan_review" in inject:
        _inject_orphan_review(rng, reviews, skus)

    if "bad_date" in inject:
        _inject_bad_date(rng, orders, user_ids, skus, products_by_sku)

    if "uncoercible_rating" in inject:
        _inject_uncoercible_rating(rng, reviews, user_ids, skus)

    return {
        "users": users,
        "products": products,
        "orders": orders,
        "reviews": reviews,
    }


def seed_shop(
    mongo_client: Any,
    *,
    inject: set[str] | None = None,
    db_name: str = "shop",
) -> dict[str, int]:
    """Drop and recreate the *shop* database with deterministic seed data.

    Parameters
    ----------
    mongo_client:
        A ``pymongo.MongoClient`` (or compatible) instance.
    inject:
        Optional set of anomaly flags to inject.  Valid values:
        ``"orphan_review"``, ``"bad_date"``, ``"uncoercible_rating"``.
    db_name:
        Name of the target database (default ``"shop"``).

    Returns
    -------
    dict[str, int]
        Mapping of collection name → inserted document count.
    """
    inject = inject or set()
    rng = _rng()

    # ------------------------------------------------------------------
    # Build documents
    # ------------------------------------------------------------------
    users = _build_users(rng, count=200)
    products = _build_products(rng, count=50)

    user_ids: list[ObjectId] = [u["_id"] for u in users]
    skus: list[str] = [p["sku"] for p in products]
    products_by_sku: dict[str, dict[str, Any]] = {p["sku"]: p for p in products}

    orders = _build_orders(rng, user_ids, skus, products_by_sku, count=500)
    reviews = _build_reviews(rng, user_ids, skus, count=300)

    # ------------------------------------------------------------------
    # Apply injections (uses continued RNG stream for determinism)
    # ------------------------------------------------------------------
    if "orphan_review" in inject:
        _inject_orphan_review(rng, reviews, skus)

    if "bad_date" in inject:
        _inject_bad_date(rng, orders, user_ids, skus, products_by_sku)

    if "uncoercible_rating" in inject:
        _inject_uncoercible_rating(rng, reviews, user_ids, skus)

    # ------------------------------------------------------------------
    # Drop + insert (idempotent)
    # ------------------------------------------------------------------
    db = mongo_client[db_name]
    db.client.drop_database(db_name)

    counts: dict[str, int] = {}
    for coll_name, docs in sorted(
        [
            ("orders", orders),
            ("products", products),
            ("reviews", reviews),
            ("users", users),
        ]
    ):
        db[coll_name].insert_many(docs)
        counts[coll_name] = len(docs)

    # Create unique indexes
    db["users"].create_index("email", unique=True)
    db["products"].create_index("sku", unique=True)

    return counts
