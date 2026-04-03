"""Admin: Slash Golf / RapidAPI request counts for the current billing month."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.slash_api_usage import get_current_month_usage

router = APIRouter()


@router.get("/slash-api-usage")
async def slash_api_usage(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Current calendar month (US Central) totals and per-endpoint breakdown.
    Counters reset automatically when the month rolls over (new DB row).
    """
    data = get_current_month_usage(db)
    limit: Optional[int] = settings.slash_api_monthly_limit
    if limit is not None and limit <= 0:
        limit = None
    out: Dict[str, Any] = {
        **data,
        "monthly_limit": limit,
    }
    if limit:
        out["percent_of_limit"] = round(
            min(100.0, (data["total_requests"] / limit) * 100.0),
            2,
        )
    else:
        out["percent_of_limit"] = None
    return out
