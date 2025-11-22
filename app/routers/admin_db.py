from fastapi import APIRouter, Depends, Query
from sqlalchemy import inspect
from typing import Any, Dict, List

from ..db import Base, engine
from ..deps import require_roles_or_token

# Ensure models are imported so Base.metadata is populated
import app.models  # noqa: F401

router = APIRouter(
    prefix="/admin/db",
    tags=["admin", "db"],
    dependencies=[Depends(require_roles_or_token(["admin"]))],
)


@router.get("/verify")
def verify_database(create: bool = Query(False, description="Create any missing ORM tables if true")) -> Dict[str, Any]:
    """
    Inspect the connected database and compare existing tables with SQLAlchemy models.

    - Returns lists of expected (from ORM) and existing (from DB) tables
    - When `create=true`, will create any missing ORM tables and re-check
    """
    insp = inspect(engine)
    existing: List[str] = sorted(insp.get_table_names(schema="public"))
    expected: List[str] = sorted(list(Base.metadata.tables.keys()))

    missing_before = sorted([t for t in expected if t not in set(existing)])

    created = False
    if create and missing_before:
        Base.metadata.create_all(bind=engine)
        insp = inspect(engine)
        existing = sorted(insp.get_table_names(schema="public"))
        created = True

    missing_after = sorted([t for t in expected if t not in set(existing)])

    return {
        "dialect": engine.dialect.name,
        "driver": getattr(engine.dialect, "driver", None),
        "expected_tables": expected,
        "existing_tables": existing,
        "missing_before": missing_before,
        "missing_after": missing_after,
        "created": created and not missing_after,
        "ok": len(missing_after) == 0,
    }
