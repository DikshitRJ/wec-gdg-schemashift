# schemashift map_hash=sha256:a6dfb0cbaaa0ab1359eb734eda0c7299de6dff4cc78daf6700c410ab03f866e6 map_version=1 generator=orm_generator
# DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP


"""Data repositories providing CRUD operations for root entities.

Spec: orm/repositories
"""

from __future__ import annotations
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from . import models

class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> Optional[models.Order]:
        return self.db.query(models.Order).filter(models.Order.id == id_).first()

    def list(self, limit: int = 100, offset: int = 0) -> List[models.Order]:
        return self.db.query(models.Order).offset(offset).limit(limit).all()

    def create(self, **kwargs: Any) -> models.Order:
        obj = models.Order(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: str) -> bool:
        obj = self.get(id_)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> Optional[models.Product]:
        return self.db.query(models.Product).filter(models.Product.id == id_).first()

    def list(self, limit: int = 100, offset: int = 0) -> List[models.Product]:
        return self.db.query(models.Product).offset(offset).limit(limit).all()

    def create(self, **kwargs: Any) -> models.Product:
        obj = models.Product(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: str) -> bool:
        obj = self.get(id_)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> Optional[models.Review]:
        return self.db.query(models.Review).filter(models.Review.id == id_).first()

    def list(self, limit: int = 100, offset: int = 0) -> List[models.Review]:
        return self.db.query(models.Review).offset(offset).limit(limit).all()

    def create(self, **kwargs: Any) -> models.Review:
        obj = models.Review(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: str) -> bool:
        obj = self.get(id_)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> Optional[models.User]:
        return self.db.query(models.User).filter(models.User.id == id_).first()

    def list(self, limit: int = 100, offset: int = 0) -> List[models.User]:
        return self.db.query(models.User).offset(offset).limit(limit).all()

    def create(self, **kwargs: Any) -> models.User:
        obj = models.User(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: str) -> bool:
        obj = self.get(id_)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
