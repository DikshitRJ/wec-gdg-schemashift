"""SQLAlchemy 2.0 ORM model and repository generator.

Spec: orm/generator
"""

from __future__ import annotations

import py_compile
from pathlib import Path

from schemashift.contracts.schema_map import SchemaMap
from schemashift.gen.header import make_python_header
from schemashift.identifiers import snake_case
from schemashift.orm.naming import column_to_attr_name, pg_type_to_python_type, table_to_class_name


def generate_orm_package(
    schema_map: SchemaMap,
    out_dir: str | Path,
) -> dict[str, str]:
    """Generate SQLAlchemy 2.0 models, repositories, and db configuration."""
    orm_dir = Path(out_dir) / "orm"
    orm_dir.mkdir(parents=True, exist_ok=True)

    header = make_python_header(schema_map.map_hash, schema_map.map_version, "orm_generator")

    # 1. Generate db.py
    db_lines = [
        header,
        '"""Database connection and session factory.',
        "",
        "Spec: orm/db",
        '"""',
        "",
        "import os",
        "from sqlalchemy import create_engine",
        "from sqlalchemy.orm import declarative_base, sessionmaker",
        "",
        'PG_URI = os.environ.get("PG_URI", "postgresql://schemashift:schemashift@localhost:5432/schemashift")',
        "# Use psycopg 3 engine URL",
        'if PG_URI.startswith("postgresql://") and "+psycopg" not in PG_URI:',
        '    ENGINE_URI = PG_URI.replace("postgresql://", "postgresql+psycopg://", 1)',
        "else:",
        "    ENGINE_URI = PG_URI",
        "",
        "engine = create_engine(ENGINE_URI, echo=False, pool_pre_ping=True)",
        "SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)",
        "Base = declarative_base()",
        "",
        "def get_db():",
        "    db = SessionLocal()",
        "    try:",
        "        yield db",
        "    finally:",
        "        db.close()",
        "",
    ]
    db_file = orm_dir / "db.py"
    db_file.write_text("\n".join(db_lines), encoding="utf-8")

    # 2. Generate models.py
    models_lines = [
        header,
        '"""SQLAlchemy 2.0 Declarative Models.',
        "",
        "Spec: orm/models",
        '"""',
        "",
        "from __future__ import annotations",
        "from datetime import datetime",
        "from decimal import Decimal",
        "from typing import Any, List, Optional",
        "from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text",
        "from sqlalchemy.dialects.postgresql import JSONB",
        "from sqlalchemy.orm import Mapped, mapped_column, relationship",
        "from .db import Base",
        "",
    ]

    for table in schema_map.tables:
        cls_name = table_to_class_name(table.name)
        models_lines.append(f"class {cls_name}(Base):")
        models_lines.append(f'    __tablename__ = "{table.name}"')
        models_lines.append("")

        for col in table.columns:
            attr_name = column_to_attr_name(col.name)
            py_type, sa_type = pg_type_to_python_type(col.pg_type)

            args: list[str] = [sa_type]
            kwargs: list[str] = [f'name="{col.name}"']
            if col.name in table.primary_key:
                kwargs.append("primary_key=True")
            if not col.nullable and col.name not in table.primary_key:
                kwargs.append("nullable=False")
            if col.nullable and col.name not in table.primary_key:
                kwargs.append("nullable=True")

            # Check if this column is a foreign key
            fk_spec = next((fk for fk in table.foreign_keys if col.name in fk.columns), None)
            if fk_spec:
                args.append(f'ForeignKey("{fk_spec.ref_table}.{fk_spec.ref_columns[0]}")')

            call_args = ", ".join(args + kwargs)
            type_hint = f"Mapped[{py_type}]" if not col.nullable else f"Mapped[Optional[{py_type}]]"
            line = f"    {attr_name}: {type_hint} = mapped_column({call_args})"
            if col.pg_type == "JSONB" or col.transform == "int_coerce":
                line += "  # REVIEW: Check JSONB / type coercion"
            models_lines.append(line)

        # Generate relationships for child tables or foreign keys
        for fk in table.foreign_keys:
            ref_cls = table_to_class_name(fk.ref_table)
            rel_name = snake_case(ref_cls)
            models_lines.append(
                f'    {rel_name} = relationship("{ref_cls}", foreign_keys=[{column_to_attr_name(fk.columns[0])}])'
            )

        models_lines.append("")

    models_file = orm_dir / "models.py"
    models_file.write_text("\n".join(models_lines), encoding="utf-8")

    # 3. Generate repositories.py
    repos_lines = [
        header,
        '"""Data repositories providing CRUD operations for root entities.',
        "",
        "Spec: orm/repositories",
        '"""',
        "",
        "from __future__ import annotations",
        "from typing import Any, List, Optional",
        "from sqlalchemy.orm import Session",
        "from . import models",
        "",
    ]

    for table in schema_map.tables:
        if table.kind != "root":
            continue
        cls_name = table_to_class_name(table.name)
        repo_name = f"{cls_name}Repository"

        repos_lines.extend(
            [
                f"class {repo_name}:",
                "    def __init__(self, db: Session) -> None:",
                "        self.db = db",
                "",
                f"    def get(self, id_: str) -> Optional[models.{cls_name}]:",
                f"        return self.db.query(models.{cls_name}).filter(models.{cls_name}.id == id_).first()",
                "",
                f"    def list(self, limit: int = 100, offset: int = 0) -> List[models.{cls_name}]:",
                f"        return self.db.query(models.{cls_name}).offset(offset).limit(limit).all()",
                "",
                f"    def create(self, **kwargs: Any) -> models.{cls_name}:",
                f"        obj = models.{cls_name}(**kwargs)",
                "        self.db.add(obj)",
                "        self.db.commit()",
                "        self.db.refresh(obj)",
                "        return obj",
                "",
                "    def delete(self, id_: str) -> bool:",
                "        obj = self.get(id_)",
                "        if obj:",
                "            self.db.delete(obj)",
                "            self.db.commit()",
                "            return True",
                "        return False",
                "",
            ]
        )

    repos_file = orm_dir / "repositories.py"
    repos_file.write_text("\n".join(repos_lines), encoding="utf-8")

    # 4. Generate crud_demo.py
    demo_lines = [
        header,
        '"""Executable smoke script demonstrating CRUD operations with generated ORM.',
        "",
        "Spec: orm/crud-demo",
        '"""',
        "",
        "import sys",
        "from datetime import datetime, timezone",
        "from pathlib import Path",
        "from bson import ObjectId",
        "",
        "_HERE = Path(__file__).resolve().parent",
        "if str(_HERE.parent) not in sys.path:",
        "    sys.path.insert(0, str(_HERE.parent))",
        "if str(_HERE) not in sys.path:",
        "    sys.path.insert(0, str(_HERE))",
        "",
        "try:",
        "    from orm.db import SessionLocal",
        "    from orm.repositories import UserRepository",
        "except ImportError:",
        "    try:",
        "        from .db import SessionLocal",
        "        from .repositories import UserRepository",
        "    except (ImportError, ValueError):",
        "        from db import SessionLocal",
        "        from repositories import UserRepository",
        "",
        "def main():",
        "    db = SessionLocal()",
        "    try:",
        "        repo = UserRepository(db)",
        "        # Test list",
        "        users = repo.list(limit=5)",
        '        print(f"Listed {len(users)} users from PostgreSQL.")',
        "        # Test create",
        "        new_id = str(ObjectId())",
        "        user = repo.create(",
        "            id=new_id,",
        '            email=f"smoke.{new_id[:6]}@example.com",',
        '            name="Smoke Test",',
        '            address_street="123 Test St",',
        '            address_city="Springfield",',
        '            address_state="IL",',
        '            address_zip="62701",',
        "            address_geo_lat=40.0,",
        "            address_geo_lng=-89.0,",
        "            prefs_newsletter=False,",
        '            prefs_theme="dark",',
        "            created_at=datetime.now(timezone.utc),",
        "        )",
        '        print(f"Created user: {user.id}")',
        "        # Test get",
        "        fetched = repo.get(new_id)",
        "        assert fetched is not None",
        '        print(f"Retrieved user: {fetched.name}")',
        "        # Test delete",
        "        deleted = repo.delete(new_id)",
        "        assert deleted",
        '        print("Deleted smoke user successfully.")',
        '        print("CRUD smoke test passed!")',
        "        return 0",
        "    finally:",
        "        db.close()",
        "",
        'if __name__ == "__main__":',
        "    sys.exit(main())",
        "",
    ]
    demo_file = orm_dir / "crud_demo.py"
    demo_file.write_text("\n".join(demo_lines), encoding="utf-8")

    # 5. Generate __init__.py
    init_lines = [
        header,
        '"""Generated SQLAlchemy 2.0 ORM package.',
        "",
        "Spec: orm/package-init",
        '"""',
        "",
        "from .db import Base, SessionLocal, engine, get_db",
        "from . import models, repositories",
        "",
    ]
    init_file = orm_dir / "__init__.py"
    init_file.write_text("\n".join(init_lines), encoding="utf-8")

    # 6. Generate app.env
    env_file = orm_dir / "app.env"
    env_file.write_text("DATA_BACKEND=sql\n", encoding="utf-8")

    # 7. Generate REFACTOR_NOTES.md
    notes_file = orm_dir / "REFACTOR_NOTES.md"
    notes_lines = [
        "# ORM Migration Refactor Notes",
        "",
        "The application data access layer has been generated with SQLAlchemy 2.0.",
        "",
        "## Review Items",
        "- Fields marked `# REVIEW:`: check JSONB and coerced numeric conversions.",
        "- Repository methods provide standard CRUD (`get`, `list`, `create`, `delete`).",
        "- Verify custom application queries and indices before production cutover.",
        "",
    ]
    notes_file.write_text("\n".join(notes_lines), encoding="utf-8")

    # Verify python files compile cleanly
    for py_file in (db_file, models_file, repos_file, demo_file, init_file):
        py_compile.compile(str(py_file), doraise=True)

    return {
        "db": str(db_file.resolve()),
        "models": str(models_file.resolve()),
        "repositories": str(repos_file.resolve()),
        "crud_demo": str(demo_file.resolve()),
    }
