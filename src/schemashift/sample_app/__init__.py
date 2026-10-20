"""Sample application layer: MongoDB CRUD and SQL stubs.

Spec: sample_app/init
"""

from schemashift.sample_app.mongo_app import MongoShopApp
from schemashift.sample_app.sql_app import SQLShopApp

__all__ = ["MongoShopApp", "SQLShopApp"]
