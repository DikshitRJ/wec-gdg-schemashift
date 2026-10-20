"""Unit tests for deterministic seed data generation.

Spec: sample/seed-test
"""

from schemashift.seed.shop import generate_shop_data


def test_seed_determinism():
    data1 = generate_shop_data()
    data2 = generate_shop_data()

    assert len(data1["users"]) == 200
    assert len(data1["products"]) == 50
    assert len(data1["orders"]) == 500
    assert len(data1["reviews"]) == 300

    # Ensure byte-identical
    assert [u["email"] for u in data1["users"]] == [u["email"] for u in data2["users"]]
    assert [p["sku"] for p in data1["products"]] == [p["sku"] for p in data2["products"]]
    assert [o["_id"] for o in data1["orders"]] == [o["_id"] for o in data2["orders"]]


def test_seed_injections():
    orphan_data = generate_shop_data(inject={"orphan_review"})
    assert len(orphan_data["reviews"]) == 301
    user_ids = {u["_id"] for u in orphan_data["users"]}
    last_review = orphan_data["reviews"][-1]
    assert last_review["userId"] not in user_ids

    bad_date_data = generate_shop_data(inject={"bad_date"})
    assert len(bad_date_data["orders"]) == 501
    assert bad_date_data["orders"][-1]["createdAt"] == "not-a-date"

    uncoercible_data = generate_shop_data(inject={"uncoercible_rating"})
    assert len(uncoercible_data["reviews"]) == 303
