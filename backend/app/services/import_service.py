"""Service for importing SmartSheet data (CSV/Excel)."""
import csv
import io
import unicodedata
import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models import Participant, Entry, Tournament, Player


class ImportService:
    """Service for importing entries and rebuys from SmartSheet exports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize a name by removing accents and special characters.
        
        Examples:
        - "Ludvig Åberg" -> "Ludvig Aberg"
        - "Nicolai Højgaard" -> "Nicolai Hojgaard"
        - "José María" -> "Jose Maria"
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name with special characters converted to ASCII equivalents
        """
        # Remove accents/diacritics using Unicode normalization
        # NFD = Normalization Form Decomposed (separates base characters from combining marks)
        normalized = unicodedata.normalize('NFD', name)
        # Remove combining characters (accents, diacritics)
        ascii_name = ''.join(
            char for char in normalized
            if unicodedata.category(char) != 'Mn'  # Mn = Mark, Nonspacing (accents)
        )
        # Convert to lowercase and strip whitespace
        return ascii_name.lower().strip()
    
    def match_player_name(self, player_name: str, tournament_id: int) -> Optional[str]:
        """
        Match a player name to a player ID.
        
        Handles special characters by normalizing them (e.g., "Ludvig Aberg" matches "Ludvig Åberg").
        
        Args:
            player_name: Player name from SmartSheet
            tournament_id: Tournament ID to search within
        
        Returns:
            Player ID if found, None otherwise
        """
        # Normalize the input name
        player_name = player_name.strip()
        normalized_input = self.normalize_name(player_name)
        
        # Try exact match first (case-insensitive)
        player = self.db.query(Player).filter(
            Player.full_name.ilike(player_name)
        ).first()
        
        if player:
            return player.player_id
        
        # Try normalized match (handles special characters)
        # Get all players and compare normalized names
        all_players = self.db.query(Player).all()
        for player in all_players:
            normalized_db = self.normalize_name(player.full_name)
            if normalized_db == normalized_input:
                return player.player_id
        
        # Try matching by first and last name separately (exact)
        name_parts = player_name.split(maxsplit=1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            player = self.db.query(Player).filter(
                Player.first_name.ilike(first_name.strip()),
                Player.last_name.ilike(last_name.strip())
            ).first()
            
            if player:
                return player.player_id
            
            # Try normalized first/last name match
            normalized_first = self.normalize_name(first_name.strip())
            normalized_last = self.normalize_name(last_name.strip())
            
            for player in all_players:
                db_first = self.normalize_name(player.first_name)
                db_last = self.normalize_name(player.last_name)
                if db_first == normalized_first and db_last == normalized_last:
                    return player.player_id
        
        # Try searching in tournament leaderboard (if available)
        from app.models import ScoreSnapshot
        snapshot = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if snapshot:
            leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
            for row in leaderboard_rows:
                first_name = row.get("firstName", "").strip()
                last_name = row.get("lastName", "").strip()
                full_name = f"{first_name} {last_name}".strip()
                
                # Exact match
                if full_name.lower() == player_name.lower():
                    return str(row.get("playerId"))
                
                # Normalized match
                normalized_db = self.normalize_name(full_name)
                if normalized_db == normalized_input:
                    return str(row.get("playerId"))
                
                # Try matching parts (exact)
                if len(name_parts) == 2:
                    if (first_name.lower() == name_parts[0].lower().strip() and
                        last_name.lower() == name_parts[1].lower().strip()):
                        return str(row.get("playerId"))
                    
                    # Try matching parts (normalized)
                    normalized_row_first = self.normalize_name(first_name)
                    normalized_row_last = self.normalize_name(last_name)
                    if (normalized_row_first == normalized_first and
                        normalized_row_last == normalized_last):
                        return str(row.get("playerId"))
        
        return None
    
    def parse_csv(self, file_content: bytes) -> List[Dict[str, str]]:
        """
        Parse CSV file content.
        
        Args:
            file_content: Raw file bytes
        
        Returns:
            List of dictionaries with column names as keys
        """
        # Try to decode as UTF-8, fallback to latin-1
        try:
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            text = file_content.decode('latin-1')
        
        # Handle different line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            # Clean up whitespace in keys and values
            cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
            rows.append(cleaned_row)
        
        return rows
    
    def validate_entries_columns(self, rows: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        Validate that entries CSV has required columns.
        
        Returns:
            (is_valid, error_message)
        """
        if not rows:
            return False, "File is empty"
        
        required_columns = [
            "Participant Name",
            "Player 1 Name",
            "Player 2 Name",
            "Player 3 Name",
            "Player 4 Name",
            "Player 5 Name",
            "Player 6 Name"
        ]
        
        first_row = rows[0]
        missing_columns = [col for col in required_columns if col not in first_row]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        return True, None
    
    def validate_rebuys_columns(self, rows: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        Validate that rebuys CSV has required columns.
        
        Returns:
            (is_valid, error_message)
        """
        if not rows:
            return False, "File is empty"
        
        required_columns = [
            "Participant Name",
            "Original Player Name",
            "Rebuy Player Name",
            "Rebuy Type"
        ]
        
        first_row = rows[0]
        missing_columns = [col for col in required_columns if col not in first_row]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        return True, None
    
    def import_entries(
        self,
        rows: List[Dict[str, str]],
        tournament_id: int
    ) -> Dict[str, Any]:
        """
        Import entries from parsed CSV rows.
        
        Args:
            rows: Parsed CSV rows
            tournament_id: Tournament ID to associate entries with
        
        Returns:
            Dictionary with import results
        """
        # Validate tournament exists
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            return {
                "success": False,
                "error": f"Tournament {tournament_id} not found"
            }
        
        # Validate columns
        is_valid, error = self.validate_entries_columns(rows)
        if not is_valid:
            return {
                "success": False,
                "error": error
            }
        
        results = {
            "success": True,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        for row_num, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            try:
                participant_name = row.get("Participant Name", "").strip()
                if not participant_name:
                    results["errors"].append({
                        "row": row_num,
                        "error": "Participant Name is required"
                    })
                    results["skipped"] += 1
                    continue
                
                # Get or create participant
                participant = self.db.query(Participant).filter(
                    Participant.name == participant_name
                ).first()
                
                if not participant:
                    participant = Participant(name=participant_name)
                    self.db.add(participant)
                    self.db.flush()  # Get ID without committing
                
                # Match player names to IDs
                player_ids = []
                player_errors = []
                
                for i in range(1, 7):
                    player_name = row.get(f"Player {i} Name", "").strip()
                    if not player_name:
                        player_errors.append(f"Player {i} Name is required")
                        continue
                    
                    player_id = self.match_player_name(player_name, tournament_id)
                    if not player_id:
                        player_errors.append(f"Player {i} '{player_name}' not found")
                        continue
                    
                    player_ids.append(player_id)
                
                if player_errors:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": "; ".join(player_errors)
                    })
                    results["skipped"] += 1
                    continue
                
                if len(player_ids) != 6:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Expected 6 players, found {len(player_ids)}"
                    })
                    results["skipped"] += 1
                    continue
                
                # Check for duplicate entry (same participant, same tournament, same players)
                existing_entry = self.db.query(Entry).filter(
                    Entry.participant_id == participant.id,
                    Entry.tournament_id == tournament_id,
                    Entry.player1_id == player_ids[0],
                    Entry.player2_id == player_ids[1],
                    Entry.player3_id == player_ids[2],
                    Entry.player4_id == player_ids[3],
                    Entry.player5_id == player_ids[4],
                    Entry.player6_id == player_ids[5]
                ).first()
                
                if existing_entry:
                    results["skipped"] += 1
                    continue
                
                # Create entry
                entry = Entry(
                    participant_id=participant.id,
                    tournament_id=tournament_id,
                    player1_id=player_ids[0],
                    player2_id=player_ids[1],
                    player3_id=player_ids[2],
                    player4_id=player_ids[3],
                    player5_id=player_ids[4],
                    player6_id=player_ids[5]
                )
                self.db.add(entry)
                results["imported"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "row": row_num,
                    "error": f"Unexpected error: {str(e)}"
                })
                results["skipped"] += 1
        
        self.db.commit()
        return results
    
    def import_rebuys(
        self,
        rows: List[Dict[str, str]],
        tournament_id: int
    ) -> Dict[str, Any]:
        """
        Import rebuys from parsed CSV rows.
        
        Args:
            rows: Parsed CSV rows
            tournament_id: Tournament ID
        
        Returns:
            Dictionary with import results
        """
        # Validate tournament exists
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            return {
                "success": False,
                "error": f"Tournament {tournament_id} not found"
            }
        
        # Validate columns
        is_valid, error = self.validate_rebuys_columns(rows)
        if not is_valid:
            return {
                "success": False,
                "error": error
            }
        
        results = {
            "success": True,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        for row_num, row in enumerate(rows, start=2):
            try:
                participant_name = row.get("Participant Name", "").strip()
                original_player_name = row.get("Original Player Name", "").strip()
                rebuy_player_name = row.get("Rebuy Player Name", "").strip()
                rebuy_type = row.get("Rebuy Type", "").strip().lower()
                
                # Validate required fields
                if not participant_name:
                    results["errors"].append({
                        "row": row_num,
                        "error": "Participant Name is required"
                    })
                    results["skipped"] += 1
                    continue
                
                if not original_player_name:
                    results["errors"].append({
                        "row": row_num,
                        "error": "Original Player Name is required"
                    })
                    results["skipped"] += 1
                    continue
                
                if not rebuy_player_name:
                    results["errors"].append({
                        "row": row_num,
                        "error": "Rebuy Player Name is required"
                    })
                    results["skipped"] += 1
                    continue
                
                # Validate rebuy type
                if rebuy_type not in ["missed_cut", "underperformer"]:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Invalid rebuy type '{rebuy_type}'. Must be 'missed_cut' or 'underperformer'"
                    })
                    results["skipped"] += 1
                    continue
                
                # Find participant
                participant = self.db.query(Participant).filter(
                    Participant.name == participant_name
                ).first()
                
                if not participant:
                    results["errors"].append({
                        "row": row_num,
                        "error": f"Participant '{participant_name}' not found. Import entries first."
                    })
                    results["skipped"] += 1
                    continue
                
                # Find entry for this participant and tournament
                entry = self.db.query(Entry).filter(
                    Entry.participant_id == participant.id,
                    Entry.tournament_id == tournament_id
                ).first()
                
                if not entry:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"No entry found for participant in tournament {tournament_id}"
                    })
                    results["skipped"] += 1
                    continue
                
                # Match original player
                original_player_id = None
                player_positions = [
                    entry.player1_id, entry.player2_id, entry.player3_id,
                    entry.player4_id, entry.player5_id, entry.player6_id
                ]
                
                # Try to match by name first
                matched_id = self.match_player_name(original_player_name, tournament_id)
                if matched_id and matched_id in player_positions:
                    original_player_id = matched_id
                else:
                    # Try direct match in entry
                    for pid in player_positions:
                        player = self.db.query(Player).filter(
                            Player.player_id == pid
                        ).first()
                        if player and player.full_name.lower() == original_player_name.lower():
                            original_player_id = pid
                            break
                
                if not original_player_id:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Original player '{original_player_name}' not found in entry"
                    })
                    results["skipped"] += 1
                    continue
                
                # Match rebuy player
                rebuy_player_id = self.match_player_name(rebuy_player_name, tournament_id)
                if not rebuy_player_id:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Rebuy player '{rebuy_player_name}' not found"
                    })
                    results["skipped"] += 1
                    continue
                
                # Initialize rebuy arrays if needed
                if entry.rebuy_player_ids is None:
                    entry.rebuy_player_ids = []
                if entry.rebuy_original_player_ids is None:
                    entry.rebuy_original_player_ids = []
                
                # Check if rebuy already exists
                if original_player_id in entry.rebuy_original_player_ids:
                    results["skipped"] += 1
                    continue
                
                # Add rebuy
                entry.rebuy_original_player_ids.append(original_player_id)
                entry.rebuy_player_ids.append(rebuy_player_id)
                entry.rebuy_type = rebuy_type
                
                # Mark JSON columns as modified so SQLAlchemy detects the change
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(entry, "rebuy_original_player_ids")
                flag_modified(entry, "rebuy_player_ids")
                
                # Set weekend bonus forfeited if underperformer
                if rebuy_type == "underperformer":
                    entry.weekend_bonus_forfeited = True
                
                results["imported"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "row": row_num,
                    "error": f"Unexpected error: {str(e)}"
                })
                results["skipped"] += 1
        
        self.db.commit()
        return results
