"""Download scoring exports (Excel workbook)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scoring_export import build_workbook, workbook_to_bytes

router = APIRouter()


@router.get("/export/scoring-workbook")
def download_scoring_workbook(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db),
):
    """
    Excel file with two sheets:

    1. **Entries & golfer points** — each pool entry, six roster slots (name, id, points
       from base + bonuses for that golfer on this entry), team/entry-level bonus, entry total.
    2. **Golfer point ledger** — every base position line per round per slot, and every
       bonus row (from the bonus_points table), with round and detail.
    """
    try:
        wb, filename = build_workbook(db, tournament_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    bio = workbook_to_bytes(wb)
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
