"""Public ranking history endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import Tournament, Entry, RankingSnapshot, Participant

router = APIRouter()


@router.get("/ranking-history/tournament/{tournament_id}")
async def get_tournament_ranking_history(
    tournament_id: int,
    round_id: Optional[int] = Query(None, description="Filter by round (optional)"),
    entry_id: Optional[int] = Query(None, description="Filter by entry (optional)"),
    db: Session = Depends(get_db)
):
    """
    Get ranking history for a tournament.
    
    Returns all ranking snapshots for the tournament, optionally filtered by round or entry.
    """
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Build query
    query = db.query(RankingSnapshot).filter(
        RankingSnapshot.tournament_id == tournament_id
    )
    
    if round_id:
        query = query.filter(RankingSnapshot.round_id == round_id)
    
    if entry_id:
        query = query.filter(RankingSnapshot.entry_id == entry_id)
    
    # Order by timestamp ascending to show progression over time
    snapshots = query.order_by(RankingSnapshot.timestamp.asc()).all()
    
    # Get entry details for response
    entry_ids = list(set(s.entry_id for s in snapshots))
    entries = db.query(Entry).filter(Entry.id.in_(entry_ids)).all()
    entry_map = {e.id: e for e in entries}
    
    # Get participant details
    participant_ids = list(set(e.participant_id for e in entries))
    participants = db.query(Participant).filter(Participant.id.in_(participant_ids)).all()
    participant_map = {p.id: p for p in participants}
    
    return {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "year": tournament.year,
        },
        "snapshots": [
            {
                "id": snapshot.id,
                "entry_id": snapshot.entry_id,
                "entry_name": participant_map.get(entry_map[snapshot.entry_id].participant_id).name if snapshot.entry_id in entry_map else "Unknown",
                "round_id": snapshot.round_id,
                "position": snapshot.position,
                "total_points": snapshot.total_points,
                "points_behind_leader": snapshot.points_behind_leader,
                "timestamp": snapshot.timestamp.isoformat(),
            }
            for snapshot in snapshots
        ],
        "total_snapshots": len(snapshots)
    }


@router.get("/ranking-history/entry/{entry_id}")
async def get_entry_ranking_history(
    entry_id: int,
    tournament_id: Optional[int] = Query(None, description="Filter by tournament (optional)"),
    db: Session = Depends(get_db)
):
    """
    Get ranking history for a specific entry.
    
    Returns all ranking snapshots showing how this entry's position changed over time.
    """
    # Verify entry exists
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Build query
    query = db.query(RankingSnapshot).filter(
        RankingSnapshot.entry_id == entry_id
    )
    
    if tournament_id:
        query = query.filter(RankingSnapshot.tournament_id == tournament_id)
    
    # Order by timestamp ascending to show progression
    snapshots = query.order_by(RankingSnapshot.timestamp.asc()).all()
    
    # Get participant details
    participant = db.query(Participant).filter(Participant.id == entry.participant_id).first()
    
    # Get tournament details
    tournament_ids = list(set(s.tournament_id for s in snapshots))
    tournaments = db.query(Tournament).filter(Tournament.id.in_(tournament_ids)).all()
    tournament_map = {t.id: t for t in tournaments}
    
    return {
        "entry": {
            "id": entry.id,
            "participant_name": participant.name if participant else "Unknown",
            "tournament_id": entry.tournament_id,
        },
        "snapshots": [
            {
                "id": snapshot.id,
                "tournament_id": snapshot.tournament_id,
                "tournament_name": tournament_map.get(snapshot.tournament_id).name if snapshot.tournament_id in tournament_map else "Unknown",
                "round_id": snapshot.round_id,
                "position": snapshot.position,
                "total_points": snapshot.total_points,
                "points_behind_leader": snapshot.points_behind_leader,
                "timestamp": snapshot.timestamp.isoformat(),
            }
            for snapshot in snapshots
        ],
        "total_snapshots": len(snapshots)
    }


@router.get("/ranking-history/analytics/{tournament_id}")
async def get_ranking_analytics(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """
    Get analytics about ranking changes for a tournament.
    
    Returns:
    - Biggest movers (entries with largest position changes)
    - Position distribution (how many entries held each position)
    - Time in lead (how long each entry held 1st place)
    """
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get all snapshots for this tournament
    snapshots = db.query(RankingSnapshot).filter(
        RankingSnapshot.tournament_id == tournament_id
    ).order_by(RankingSnapshot.timestamp.asc()).all()
    
    if not snapshots:
        return {
            "tournament_id": tournament_id,
            "biggest_movers": [],
            "position_distribution": {},
            "time_in_lead": {},
            "message": "No ranking snapshots found for this tournament"
        }
    
    # Get entry and participant details
    entry_ids = list(set(s.entry_id for s in snapshots))
    entries = db.query(Entry).filter(Entry.id.in_(entry_ids)).all()
    entry_map = {e.id: e for e in entries}
    
    participant_ids = list(set(e.participant_id for e in entries))
    participants = db.query(Participant).filter(Participant.id.in_(participant_ids)).all()
    participant_map = {p.id: p for p in participants}
    
    # Calculate biggest movers
    # Find first and last position for each entry
    entry_positions = {}
    for snapshot in snapshots:
        entry_id = snapshot.entry_id
        if entry_id not in entry_positions:
            entry_positions[entry_id] = {
                "first_position": snapshot.position,
                "first_timestamp": snapshot.timestamp,
                "last_position": snapshot.position,
                "last_timestamp": snapshot.timestamp,
            }
        else:
            if snapshot.timestamp < entry_positions[entry_id]["first_timestamp"]:
                entry_positions[entry_id]["first_position"] = snapshot.position
                entry_positions[entry_id]["first_timestamp"] = snapshot.timestamp
            if snapshot.timestamp > entry_positions[entry_id]["last_timestamp"]:
                entry_positions[entry_id]["last_position"] = snapshot.position
                entry_positions[entry_id]["last_timestamp"] = snapshot.timestamp
    
    biggest_movers = []
    for entry_id, positions in entry_positions.items():
        position_change = positions["first_position"] - positions["last_position"]
        if position_change != 0:  # Only include entries that moved
            entry = entry_map.get(entry_id)
            participant = participant_map.get(entry.participant_id) if entry else None
            biggest_movers.append({
                "entry_id": entry_id,
                "entry_name": participant.name if participant else "Unknown",
                "start_position": positions["first_position"],
                "end_position": positions["last_position"],
                "position_change": position_change,
                "improvement": position_change > 0,  # Positive change = improvement (lower position number)
            })
    
    # Sort by absolute position change
    biggest_movers.sort(key=lambda x: abs(x["position_change"]), reverse=True)
    
    # Calculate position distribution
    position_distribution = {}
    for snapshot in snapshots:
        position = snapshot.position
        if position not in position_distribution:
            position_distribution[position] = {
                "position": position,
                "unique_entries": set(),
                "total_snapshots": 0
            }
        position_distribution[position]["unique_entries"].add(snapshot.entry_id)
        position_distribution[position]["total_snapshots"] += 1
    
    # Convert sets to counts
    position_dist = {}
    for pos, data in position_distribution.items():
        entry_names = [
            participant_map.get(entry_map[eid].participant_id).name 
            if eid in entry_map and entry_map[eid].participant_id in participant_map 
            else "Unknown"
            for eid in data["unique_entries"]
        ]
        position_dist[pos] = {
            "position": pos,
            "unique_entries_count": len(data["unique_entries"]),
            "unique_entries": entry_names,
            "total_snapshots": data["total_snapshots"]
        }
    
    # Calculate time in lead (entries that held position 1)
    time_in_lead = {}
    lead_snapshots = [s for s in snapshots if s.position == 1]
    
    if lead_snapshots:
        # Group consecutive snapshots by entry
        current_entry = None
        current_start = None
        for snapshot in lead_snapshots:
            if snapshot.entry_id != current_entry:
                # New entry in lead
                if current_entry is not None:
                    # Calculate duration for previous entry
                    duration = (snapshot.timestamp - current_start).total_seconds()
                    if current_entry not in time_in_lead:
                        time_in_lead[current_entry] = 0
                    time_in_lead[current_entry] += duration
                
                current_entry = snapshot.entry_id
                current_start = snapshot.timestamp
            else:
                # Same entry still in lead, update end time
                pass
        
        # Handle last entry
        if current_entry is not None and len(lead_snapshots) > 0:
            last_snapshot = lead_snapshots[-1]
            duration = (last_snapshot.timestamp - current_start).total_seconds()
            if current_entry not in time_in_lead:
                time_in_lead[current_entry] = 0
            time_in_lead[current_entry] += duration
        
        # Convert to hours and format
        time_in_lead_formatted = {}
        for entry_id, seconds in time_in_lead.items():
            entry = entry_map.get(entry_id)
            participant = participant_map.get(entry.participant_id) if entry else None
            hours = seconds / 3600
            time_in_lead_formatted[entry_id] = {
                "entry_id": entry_id,
                "entry_name": participant.name if participant else "Unknown",
                "seconds": seconds,
                "hours": round(hours, 2),
                "formatted": f"{int(hours)}h {int((seconds % 3600) / 60)}m"
            }
    
    return {
        "tournament_id": tournament_id,
        "tournament_name": tournament.name,
        "biggest_movers": biggest_movers[:10],  # Top 10
        "position_distribution": position_dist,
        "time_in_lead": list(time_in_lead_formatted.values()),
        "total_snapshots": len(snapshots)
    }
