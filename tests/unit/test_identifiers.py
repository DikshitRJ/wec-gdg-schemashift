"""Unit tests for SQL identifier helpers.

Spec: foundation/identifiers-test
"""

from schemashift.identifiers import (
    pluralize,
    quote_ident,
    safe_name,
    singularize,
    snake_case,
)


def test_quote_ident():
    assert quote_ident("users") == '"users"'
    assert quote_ident('my"table') == '"my""table"'


def test_snake_case():
    assert snake_case("camelCase") == "camel_case"
    assert snake_case("PascalCase") == "pascal_case"
    assert snake_case("kebab-case") == "kebab_case"
    assert snake_case("some string") == "some_string"
    assert snake_case("userId") == "user_id"


def test_safe_name():
    assert safe_name("123bad") == "col_123bad"
    assert safe_name("User@Name!#") == "user_name"
    assert safe_name("a" * 100) == "a" * 63


def test_pluralize_and_singularize():
    assert pluralize("user") == "users"
    assert pluralize("category") == "categories"
    assert pluralize("box") == "boxes"
    assert singularize("users") == "user"
    assert singularize("categories") == "category"
    assert singularize("boxes") == "box"
