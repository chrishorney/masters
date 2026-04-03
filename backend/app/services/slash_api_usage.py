"""Record and read Slash Golf API usage per calendar month (US Central)."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.models import SlashApiUsageMonthly

logger = logging.getLogger(__name__)

CENTRAL_TZ = ZoneInfo("America/Chicago")


def current_billing_month() -> Tuple[int, int]:
    """Return (year, month) for the current calendar month in Central Time."""
    now = datetime.now(CENTRAL_TZ)
    return now.year, now.month


def _endpoint_key(endpoint: str) -> str:
    if not endpoint:
        return "unknown"
    parts = [p for p in endpoint.strip().split("/") if p]
    return parts[-1] if parts else "unknown"


def record_slash_api_request(endpoint: str) -> None:
    """
    Increment counters for the current Central month after a successful Slash API call.
    Never raises — failures are logged only so API traffic is never blocked by metrics.
    """
    key = _endpoint_key(endpoint)
    y, m = current_billing_month()

    db: Optional[Session] = None
    try:
        db = SessionLocal()
    except Exception as e:
        logger.warning("slash_api_usage: could not open session: %s", e)
        return

    try:
        for _ in range(6):
            try:
                row = (
                    db.query(SlashApiUsageMonthly)
                    .filter(
                        SlashApiUsageMonthly.year == y,
                        SlashApiUsageMonthly.month == m,
                    )
                    .with_for_update(of=SlashApiUsageMonthly)
                    .first()
                )
                if row is None:
                    row = SlashApiUsageMonthly(
                        year=y,
                        month=m,
                        total_requests=0,
                        by_endpoint={},
                    )
                    db.add(row)
                    try:
                        db.flush()
                    except IntegrityError:
                        db.rollback()
                        continue

                row.total_requests = int(row.total_requests or 0) + 1
                ep = dict(row.by_endpoint or {})
                ep[key] = int(ep.get(key, 0)) + 1
                row.by_endpoint = ep
                db.commit()
                return
            except IntegrityError:
                db.rollback()
                continue
    except Exception as e:
        logger.warning("slash_api_usage: failed to record hit for %s: %s", key, e)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        try:
            db.close()
        except Exception:
            pass


def get_current_month_usage(db: Session) -> Dict[str, Any]:
    y, m = current_billing_month()
    row = (
        db.query(SlashApiUsageMonthly)
        .filter(
            SlashApiUsageMonthly.year == y,
            SlashApiUsageMonthly.month == m,
        )
        .first()
    )
    by_ep = dict(row.by_endpoint or {}) if row else {}
    return {
        "year": y,
        "month": m,
        "timezone": "America/Chicago",
        "total_requests": int(row.total_requests) if row else 0,
        "by_endpoint": by_ep,
    }
