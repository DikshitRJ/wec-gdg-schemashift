# schemashift map_hash=sha256:a6dfb0cbaaa0ab1359eb734eda0c7299de6dff4cc78daf6700c410ab03f866e6 map_version=1 generator=orm_generator
# DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP


"""SQLAlchemy 2.0 Declarative Models.

Spec: orm/models
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(Text, name="id", primary_key=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(Text, name="coupon_code", nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), name="created_at", nullable=False)
    shipping_address_city: Mapped[str] = mapped_column(Text, name="shipping_address_city", nullable=False)
    shipping_address_state: Mapped[str] = mapped_column(Text, name="shipping_address_state", nullable=False)
    shipping_address_street: Mapped[str] = mapped_column(Text, name="shipping_address_street", nullable=False)
    shipping_address_zip: Mapped[str] = mapped_column(Text, name="shipping_address_zip", nullable=False)
    shipping_carrier: Mapped[str] = mapped_column(Text, name="shipping_carrier", nullable=False)
    shipping_tracking_no: Mapped[str] = mapped_column(Text, name="shipping_tracking_no", nullable=False)
    status: Mapped[str] = mapped_column(Text, name="status", nullable=False)
    user_id: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), name="user_id", nullable=False)
    user = relationship("User", foreign_keys=[user_id])

class OrdersItem(Base):
    __tablename__ = "orders_items"

    id: Mapped[int] = mapped_column(BigInteger, name="id", primary_key=True)
    order_id: Mapped[str] = mapped_column(Text, ForeignKey("orders.id"), name="order_id", nullable=False)
    position: Mapped[int] = mapped_column(Integer, name="position", nullable=False)
    qty: Mapped[int] = mapped_column(Integer, name="qty", nullable=False)
    sku: Mapped[str] = mapped_column(Text, name="sku", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric, name="unit_price", nullable=False)
    order = relationship("Order", foreign_keys=[order_id])

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(Text, name="id", primary_key=True)
    attrs: Mapped[dict[str, Any]] = mapped_column(JSONB, name="attrs", nullable=False)  # REVIEW: Check JSONB / type coercion
    description: Mapped[str] = mapped_column(Text, name="description", nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, name="in_stock", nullable=False)
    name: Mapped[str] = mapped_column(Text, name="name", nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric, name="price", nullable=False)
    sku: Mapped[str] = mapped_column(Text, name="sku", nullable=False)

class ProductsCategory(Base):
    __tablename__ = "products_categories"

    id: Mapped[int] = mapped_column(BigInteger, name="id", primary_key=True)
    product_id: Mapped[str] = mapped_column(Text, ForeignKey("products.id"), name="product_id", nullable=False)
    position: Mapped[int] = mapped_column(Integer, name="position", nullable=False)
    value: Mapped[str] = mapped_column(Text, name="value", nullable=False)
    product = relationship("Product", foreign_keys=[product_id])

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(Text, name="id", primary_key=True)
    body: Mapped[str] = mapped_column(Text, name="body", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), name="created_at", nullable=False)
    product_sku: Mapped[str] = mapped_column(Text, ForeignKey("products.sku"), name="product_sku", nullable=False)
    rating: Mapped[int] = mapped_column(Integer, name="rating", nullable=False)  # REVIEW: Check JSONB / type coercion
    title: Mapped[str] = mapped_column(Text, name="title", nullable=False)
    user_id: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), name="user_id", nullable=False)
    product = relationship("Product", foreign_keys=[product_sku])
    user = relationship("User", foreign_keys=[user_id])

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, name="id", primary_key=True)
    address_city: Mapped[str] = mapped_column(Text, name="address_city", nullable=False)
    address_geo_lat: Mapped[float] = mapped_column(Float, name="address_geo_lat", nullable=False)
    address_geo_lng: Mapped[float] = mapped_column(Float, name="address_geo_lng", nullable=False)
    address_state: Mapped[str] = mapped_column(Text, name="address_state", nullable=False)
    address_street: Mapped[str] = mapped_column(Text, name="address_street", nullable=False)
    address_zip: Mapped[str] = mapped_column(Text, name="address_zip", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), name="created_at", nullable=False)
    email: Mapped[str] = mapped_column(Text, name="email", nullable=False)
    name: Mapped[str] = mapped_column(Text, name="name", nullable=False)
    prefs_newsletter: Mapped[bool] = mapped_column(Boolean, name="prefs_newsletter", nullable=False)
    prefs_theme: Mapped[str] = mapped_column(Text, name="prefs_theme", nullable=False)

class UsersTag(Base):
    __tablename__ = "users_tags"

    id: Mapped[int] = mapped_column(BigInteger, name="id", primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), name="user_id", nullable=False)
    position: Mapped[int] = mapped_column(Integer, name="position", nullable=False)
    value: Mapped[str] = mapped_column(Text, name="value", nullable=False)
    user = relationship("User", foreign_keys=[user_id])
