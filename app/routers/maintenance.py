from fastapi import APIRouter, Depends, Query
from app.deps import require_roles_or_token
from app.services.partition_service import ensure_current_month_partitions, prune_old_partitions

router = APIRouter(prefix="/v1/maintenance", tags=["maintenance"])

@router.post("/partition/ensure_current")
def ensure_current_partition(user=Depends(require_roles_or_token(["admin"]))):
    created = ensure_current_month_partitions()
    return {"ok": True, "created": created}


@router.post("/partitions/prune")
def prune_partitions(months: int = Query(6, ge=1, le=60), user=Depends(require_roles_or_token(["admin"]))):
    """Prune old partitions. For SQLite or non-partitioned DBs, returns ok without action."""
    pruned = prune_old_partitions(months=months)
    return {"ok": True, "pruned": pruned}
