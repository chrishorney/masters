"""Service for importing SmartSheet data (CSV/Excel)."""
import csv
import io
import unicodedata
import re
import difflib
import zipfile
from xml.etree import ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models import Participant, Entry, Tournament, Player


class ImportService:
    """Service for importing entries and rebuys from SmartSheet exports."""
    
    def __init__(self, db: Session):
        self.db = db
        # Populated by parse_csv() so we can use column order when SmartSheet exports
        # repeat header names (e.g. multiple "Replace" columns).
        self._parsed_header_keys: List[str] = []
    
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

    def _get_candidate_players(self, tournament_id: int) -> List[Tuple[str, str]]:
        """Return list of (full_name, player_id) for fuzzy matching (Player table + tournament leaderboard)."""
        candidates: List[Tuple[str, str]] = []
        seen_ids = set()
        for p in self.db.query(Player).all():
            key = (p.full_name.strip(), p.player_id)
            if p.player_id not in seen_ids:
                candidates.append(key)
                seen_ids.add(p.player_id)
        from app.models import ScoreSnapshot
        snapshot = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        if snapshot:
            for row in snapshot.leaderboard_data.get("leaderboardRows", []):
                first = (row.get("firstName") or "").strip()
                last = (row.get("lastName") or "").strip()
                full = f"{first} {last}".strip()
                pid = str(row.get("playerId", ""))
                if pid and pid not in seen_ids and full:
                    candidates.append((full, pid))
                    seen_ids.add(pid)
        return candidates

    def suggest_player_name(self, player_name: str, tournament_id: int) -> Optional[Tuple[str, str]]:
        """
        If the name doesn't match exactly, suggest the closest match (e.g. Jordan Speith -> Jordan Spieth).
        Returns (suggested_full_name, player_id) or None if no good suggestion.
        """
        player_name = player_name.strip()
        if not player_name:
            return None
        if self.match_player_name(player_name, tournament_id):
            return None  # Already matches
        candidates = self._get_candidate_players(tournament_id)
        if not candidates:
            return None
        names = [c[0] for c in candidates]
        normalized_input = self.normalize_name(player_name)
        normalized_names = [self.normalize_name(n) for n in names]
        matches = difflib.get_close_matches(normalized_input, normalized_names, n=1, cutoff=0.8)
        if not matches:
            return None
        idx = normalized_names.index(matches[0])
        return candidates[idx]  # (full_name, player_id)

    def validate_entries_for_import(
        self, rows: List[Dict[str, str]], tournament_id: int
    ) -> Dict[str, Any]:
        """
        Validate entries CSV and return suggestions for any player name that didn't match.
        Does not write to DB. Returns structure for frontend to show "Did you mean X?" and then
        re-submit with applied_suggestions.
        """
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            return {"valid": False, "error": f"Tournament {tournament_id} not found", "row_results": [], "suggestions": []}
        is_valid, col_error = self.validate_entries_columns(rows)
        if not is_valid:
            return {"valid": False, "error": col_error, "row_results": [], "suggestions": []}
        row_results: List[Dict[str, Any]] = []
        all_suggestions: List[Dict[str, Any]] = []
        first_row = rows[0]
        keys = set(first_row.keys())

        def has_key_variant(base: str) -> bool:
            return any((k == base or k.startswith(base + "__")) for k in keys)

        # Support both template and SmartSheet headers.
        participant_key = "Participant Name" if has_key_variant("Participant Name") else "Player Name"
        professional_keys = []
        for i in range(1, 7):
            template_key = f"Player {i} Name"
            smart_key = f"Professional {i}"
            # Prefer template keys if present, otherwise fall back to SmartSheet "Professional X"
            if has_key_variant(template_key):
                # We want the exact key (including any __ suffix for duplicates).
                k = next(k for k in keys if k == template_key or k.startswith(template_key + "__"))
                professional_keys.append(k)
            else:
                k = next(k for k in keys if k == smart_key or k.startswith(smart_key + "__"))
                professional_keys.append(k)

        for row_num, row in enumerate(rows, start=2):
            participant_name = (row.get(participant_key) or "").strip()
            if not participant_name:
                row_results.append({"row": row_num, "participant": "", "players": [], "row_error": "Participant Name is required"})
                continue
            players: List[Dict[str, Any]] = []
            row_ok = True
            for i in range(1, 7):
                col = f"Player {i} Name"
                actual_header_key = professional_keys[i - 1]
                value = (row.get(actual_header_key) or "").strip()
                if not value:
                    players.append({"column": col, "value": value, "matched": False, "player_id": None, "suggestion": None})
                    row_ok = False
                    continue
                player_id = self.match_player_name(value, tournament_id)
                if player_id:
                    players.append({"column": col, "value": value, "matched": True, "player_id": player_id, "suggestion": None})
                    continue
                suggestion = self.suggest_player_name(value, tournament_id)
                if suggestion:
                    suggested_name, suggested_id = suggestion
                    players.append({"column": col, "value": value, "matched": False, "player_id": None, "suggestion": {"name": suggested_name, "player_id": suggested_id}})
                    all_suggestions.append({"row": row_num, "column": col, "value": value, "suggestion": suggested_name, "player_id": suggested_id})
                else:
                    players.append({"column": col, "value": value, "matched": False, "player_id": None, "suggestion": None})
                    row_ok = False
            row_results.append({"row": row_num, "participant": participant_name, "players": players, "row_error": None if row_ok else "Unmatched player name(s)"})
        # Can import directly if every row has all 6 players matched (no suggestions needed)
        rows_without_error = [r for r in row_results if not r.get("row_error")]
        can_import_directly = (
            len(rows_without_error) > 0
            and all(len(r.get("players", [])) == 6 and all(p.get("matched") for p in r.get("players", [])) for r in rows_without_error)
        )
        # Can import with corrections if every unmatched player has a suggestion
        can_import_with_corrections = len(all_suggestions) > 0 and all(
            all(p.get("matched") or p.get("suggestion") for p in r.get("players", []))
            for r in row_results
        )
        return {
            "valid": can_import_directly or can_import_with_corrections or not any(r.get("row_error") for r in row_results),
            "error": None,
            "row_results": row_results,
            "suggestions": all_suggestions,
            "can_import_directly": can_import_directly,
            "can_import_with_corrections": can_import_with_corrections,
        }

    def validate_rebuys_for_import(
        self, rows: List[Dict[str, str]], tournament_id: int
    ) -> Dict[str, Any]:
        """
        Validate rebuys CSV and return suggestions for Original Player Name and Rebuy Player Name.
        Original player is suggested only from the entry's 6 players; rebuy player from full candidate list.
        """
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            return {
                "valid": False,
                "error": f"Tournament {tournament_id} not found",
                "row_results": [],
                "suggestions": [],
                "can_import_directly": False,
                "can_import_with_corrections": False,
            }

        header_keys = getattr(self, "_parsed_header_keys", []) or []
        pro6_key = next((k for k in header_keys if k == "Professional 6" or k.startswith("Professional 6__")), None)
        is_smart_sheet_rebuys = bool(pro6_key)

        if is_smart_sheet_rebuys:
            first_row = rows[0] if rows else {}
            keys = set(first_row.keys())

            def has_key_variant(base: str) -> bool:
                return any((k == base or k.startswith(base + "__")) for k in keys)

            participant_key = "Participant Name" if has_key_variant("Participant Name") else "Player Name"
            pro6_idx = header_keys.index(pro6_key)
            replace_start_idx = pro6_idx + 1
            replace_pairs: List[Tuple[str, str]] = []
            for pair_idx in range(6):
                a = replace_start_idx + pair_idx * 2
                b = a + 1
                if b >= len(header_keys):
                    break
                replace_pairs.append((header_keys[a], header_keys[b]))

            row_results: List[Dict[str, Any]] = []
            all_suggestions: List[Dict[str, Any]] = []

            for row_num, row in enumerate(rows, start=2):
                participant_name = (row.get(participant_key) or "").strip()
                row_error = None

                if not participant_name:
                    row_results.append({"row": row_num, "participant": "", "row_error": "Participant Name is required"})
                    continue

                participant = self.db.query(Participant).filter(Participant.name == participant_name).first()
                if not participant:
                    row_results.append({
                        "row": row_num,
                        "participant": participant_name,
                        "row_error": "Participant not found. Import entries first."
                    })
                    continue

                entry = self.db.query(Entry).filter(
                    Entry.participant_id == participant.id,
                    Entry.tournament_id == tournament_id,
                ).first()

                if not entry:
                    row_results.append({
                        "row": row_num,
                        "participant": participant_name,
                        "row_error": "No entry for this participant in tournament."
                    })
                    continue

                player_positions = [
                    entry.player1_id,
                    entry.player2_id,
                    entry.player3_id,
                    entry.player4_id,
                    entry.player5_id,
                    entry.player6_id,
                ]

                found_any_pair = False
                for pair_idx, (orig_key, with_key) in enumerate(replace_pairs):
                    orig_name = (row.get(orig_key) or "").strip()
                    with_name = (row.get(with_key) or "").strip()

                    # Treat completely empty pair as "not provided"
                    if not orig_name and not with_name:
                        continue

                    found_any_pair = True

                    if not orig_name and with_name:
                        row_error = f"Missing Replace Original for replace pair {pair_idx + 1}"
                        break

                    # Resolve original player (must be one of the 6 entry players)
                    original_player_id = self.match_player_name(orig_name, tournament_id)
                    if original_player_id and original_player_id in player_positions:
                        pass
                    else:
                        suggestion = self.suggest_player_name(orig_name, tournament_id)
                        if suggestion:
                            sug_name, sug_id = suggestion
                            if sug_id in player_positions:
                                all_suggestions.append({
                                    "row": row_num,
                                    "column": f"Replace Original {pair_idx + 1}",
                                    "value": orig_name,
                                    "suggestion": sug_name,
                                    "player_id": sug_id,
                                })
                            else:
                                row_error = f"Original player '{orig_name}' not found in entry"
                                break
                        else:
                            row_error = f"Original player '{orig_name}' not found in entry"
                            break

                    # Resolve replacement player (can be any tournament player)
                    replacement_player_id = self.match_player_name(with_name, tournament_id)
                    if replacement_player_id:
                        pass
                    else:
                        suggestion = self.suggest_player_name(with_name, tournament_id)
                        if suggestion:
                            sug_name, sug_id = suggestion
                            all_suggestions.append({
                                "row": row_num,
                                "column": f"Replace With {pair_idx + 1}",
                                "value": with_name,
                                "suggestion": sug_name,
                                "player_id": sug_id,
                            })
                        else:
                            row_error = f"Rebuy player '{with_name}' not found"
                            break

                if not found_any_pair and not row_error:
                    row_error = "No replace pairs found for this participant"

                row_results.append({
                    "row": row_num,
                    "participant": participant_name,
                    "row_error": row_error,
                })

            valid = not any(r.get("row_error") for r in row_results)
            can_import_directly = valid and len(all_suggestions) == 0
            can_import_with_corrections = valid and len(all_suggestions) > 0
            return {
                "valid": valid,
                "error": None,
                "row_results": row_results,
                "suggestions": all_suggestions,
                "can_import_directly": can_import_directly,
                "can_import_with_corrections": can_import_with_corrections,
            }

        # Normalized format (legacy): Participant Name, Original Player Name, Rebuy Player Name
        is_valid, col_error = self.validate_rebuys_columns(rows)
        if not is_valid:
            return {
                "valid": False,
                "error": col_error,
                "row_results": [],
                "suggestions": [],
                "can_import_directly": False,
                "can_import_with_corrections": False,
            }

        row_results: List[Dict[str, Any]] = []
        all_suggestions: List[Dict[str, Any]] = []
        for row_num, row in enumerate(rows, start=2):
            participant_name = (row.get("Participant Name") or "").strip()
            original_name = (row.get("Original Player Name") or "").strip()
            rebuy_name = (row.get("Rebuy Player Name") or "").strip()
            row_error = None

            if not participant_name:
                row_results.append({"row": row_num, "participant": "", "original": None, "rebuy": None, "row_error": "Participant Name is required"})
                continue

            participant = self.db.query(Participant).filter(Participant.name == participant_name).first()
            if not participant:
                row_results.append({"row": row_num, "participant": participant_name, "original": None, "rebuy": None, "row_error": "Participant not found. Import entries first."})
                continue

            entry = self.db.query(Entry).filter(
                Entry.participant_id == participant.id,
                Entry.tournament_id == tournament_id,
            ).first()

            if not entry:
                row_results.append({"row": row_num, "participant": participant_name, "original": None, "rebuy": None, "row_error": "No entry for this participant in tournament."})
                continue

            if not original_name:
                row_results.append({"row": row_num, "participant": participant_name, "original": None, "rebuy": None, "row_error": "Original Player Name is required."})
                continue

            if not rebuy_name:
                row_results.append({"row": row_num, "participant": participant_name, "original": None, "rebuy": None, "row_error": "Rebuy Player Name is required."})
                continue

            player_positions = [entry.player1_id, entry.player2_id, entry.player3_id, entry.player4_id, entry.player5_id, entry.player6_id]
            original_matched = self.match_player_name(original_name, tournament_id)
            if original_matched and original_matched in player_positions:
                original_status = {"column": "Original Player Name", "value": original_name, "matched": True, "player_id": original_matched, "suggestion": None}
            else:
                entry_player_names = []
                for pid in player_positions:
                    p = self.db.query(Player).filter(Player.player_id == pid).first()
                    if p:
                        entry_player_names.append((p.full_name, p.player_id))
                if not entry_player_names:
                    for pid in player_positions:
                        entry_player_names.append((str(pid), pid))
                names_only = [x[0] for x in entry_player_names]
                normalized_input = self.normalize_name(original_name)
                normalized_candidates = [self.normalize_name(n) for n in names_only]
                matches = difflib.get_close_matches(normalized_input, normalized_candidates, n=1, cutoff=0.8)
                if matches:
                    idx = normalized_candidates.index(matches[0])
                    sug_name, sug_id = entry_player_names[idx]
                    original_status = {"column": "Original Player Name", "value": original_name, "matched": False, "player_id": None, "suggestion": {"name": sug_name, "player_id": sug_id}}
                    all_suggestions.append({"row": row_num, "column": "Original Player Name", "value": original_name, "suggestion": sug_name, "player_id": sug_id})
                else:
                    original_status = {"column": "Original Player Name", "value": original_name, "matched": False, "player_id": None, "suggestion": None}
                    row_error = row_error or f"Original player '{original_name}' not found in entry"

            rebuy_matched = self.match_player_name(rebuy_name, tournament_id)
            if rebuy_matched:
                rebuy_status = {"column": "Rebuy Player Name", "value": rebuy_name, "matched": True, "player_id": rebuy_matched, "suggestion": None}
            else:
                suggestion = self.suggest_player_name(rebuy_name, tournament_id)
                if suggestion:
                    sug_name, sug_id = suggestion
                    rebuy_status = {"column": "Rebuy Player Name", "value": rebuy_name, "matched": False, "player_id": None, "suggestion": {"name": sug_name, "player_id": sug_id}}
                    all_suggestions.append({"row": row_num, "column": "Rebuy Player Name", "value": rebuy_name, "suggestion": sug_name, "player_id": sug_id})
                else:
                    rebuy_status = {"column": "Rebuy Player Name", "value": rebuy_name, "matched": False, "player_id": None, "suggestion": None}
                    row_error = row_error or f"Rebuy player '{rebuy_name}' not found"

            row_results.append({"row": row_num, "participant": participant_name, "original": original_status, "rebuy": rebuy_status, "row_error": row_error})

        valid = not any(r.get("row_error") for r in row_results)
        can_import_directly = valid and len(all_suggestions) == 0
        can_import_with_corrections = valid and len(all_suggestions) > 0
        return {
            "valid": valid,
            "error": None,
            "row_results": row_results,
            "suggestions": all_suggestions,
            "can_import_directly": can_import_directly,
            "can_import_with_corrections": can_import_with_corrections,
        }
    
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

        # Use csv.reader so we can preserve duplicate headers by disambiguating them.
        # csv.DictReader would silently overwrite duplicate keys.
        reader = csv.reader(io.StringIO(text))
        all_rows = list(reader)
        return self._rows_to_dicts(all_rows)

    def parse_file(self, file_content: bytes, filename: str) -> List[Dict[str, str]]:
        """
        Parse an uploaded tabular file into row dictionaries.

        Supports:
        - .csv
        - .xlsx / .xlsm (Excel)
        """
        lower_name = (filename or "").lower()
        if lower_name.endswith(".csv"):
            return self.parse_csv(file_content)
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xlsm"):
            return self.parse_excel(file_content)
        raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")

    def parse_excel(self, file_content: bytes) -> List[Dict[str, str]]:
        """Parse Excel workbook bytes (first worksheet) into row dictionaries."""
        try:
            workbook_zip = zipfile.ZipFile(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError("Invalid Excel file (.xlsx/.xlsm).") from e

        # Shared strings table (optional in xlsx).
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            shared_xml = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for si in shared_xml.findall(".//{*}si"):
                # Can be <si><t>.. or rich text runs <r><t>..
                text_parts = []
                for t in si.findall(".//{*}t"):
                    text_parts.append(t.text or "")
                shared_strings.append("".join(text_parts))

        # Read first worksheet; SmartSheet exports place data here.
        sheet_path = "xl/worksheets/sheet1.xml"
        if sheet_path not in workbook_zip.namelist():
            # Fallback: first worksheet-like file we can find.
            sheet_candidates = sorted(
                [n for n in workbook_zip.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            )
            if not sheet_candidates:
                raise ValueError("Excel file has no worksheet data.")
            sheet_path = sheet_candidates[0]

        sheet_xml = ET.fromstring(workbook_zip.read(sheet_path))

        # Build sparse rows keyed by column index from cell refs like "A1", "BC12".
        all_rows: List[List[str]] = []
        for row_el in sheet_xml.findall(".//{*}sheetData/{*}row"):
            row_values: Dict[int, str] = {}
            max_col = -1
            for cell in row_el.findall("{*}c"):
                ref = cell.attrib.get("r", "")
                col_idx = self._excel_ref_to_col_index(ref)
                if col_idx is None:
                    continue

                max_col = max(max_col, col_idx)
                cell_type = cell.attrib.get("t", "")
                value_el = cell.find("{*}v")
                inline_el = cell.find("{*}is/{*}t")

                value = ""
                if cell_type == "s" and value_el is not None and value_el.text is not None:
                    try:
                        ss_idx = int(value_el.text)
                        value = shared_strings[ss_idx] if 0 <= ss_idx < len(shared_strings) else ""
                    except Exception:
                        value = ""
                elif inline_el is not None and inline_el.text is not None:
                    value = inline_el.text
                elif value_el is not None and value_el.text is not None:
                    value = value_el.text

                row_values[col_idx] = (value or "").strip()

            if max_col >= 0:
                materialized = ["" for _ in range(max_col + 1)]
                for idx, val in row_values.items():
                    materialized[idx] = val
                all_rows.append(materialized)

        return self._rows_to_dicts(all_rows)

    def _excel_ref_to_col_index(self, ref: str) -> Optional[int]:
        """Convert Excel cell ref (e.g. A1, BC12) to zero-based column index."""
        if not ref:
            return None
        match = re.match(r"^([A-Za-z]+)\d+$", ref)
        if not match:
            return None
        letters = match.group(1).upper()
        idx = 0
        for ch in letters:
            idx = idx * 26 + (ord(ch) - ord("A") + 1)
        return idx - 1

    def _rows_to_dicts(self, all_rows: List[List[str]]) -> List[Dict[str, str]]:
        """
        Convert a matrix of rows (header + data rows) into dictionaries while
        preserving duplicate header names with __N suffixes.
        """
        if not all_rows:
            self._parsed_header_keys = []
            return []

        raw_header = all_rows[0]
        header_counts: Dict[str, int] = {}
        unique_header: List[str] = []
        for h in raw_header:
            base = (h or "").strip()
            if base in header_counts:
                header_counts[base] += 1
                unique_header.append(f"{base}__{header_counts[base]}")
            else:
                header_counts[base] = 1
                unique_header.append(base)

        self._parsed_header_keys = unique_header

        parsed: List[Dict[str, str]] = []
        for row in all_rows[1:]:
            # Skip completely blank rows
            if not any((c or "").strip() for c in row):
                continue

            # Pad/truncate to header length
            padded = (row + [""] * len(unique_header))[: len(unique_header)]
            cleaned_row = {}
            for i, key in enumerate(unique_header):
                v = padded[i] if i < len(padded) else ""
                cleaned_row[key] = v.strip() if v else ""
            parsed.append(cleaned_row)

        return parsed
    
    def validate_entries_columns(self, rows: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        Validate that entries CSV has required columns.
        
        Returns:
            (is_valid, error_message)
        """
        if not rows:
            return False, "File is empty"
        
        first_row = rows[0]
        keys = set(first_row.keys())

        # Support both the internal template and raw SmartSheet exports.
        # Internal template:
        template_required = [
            "Participant Name",
            "Player 1 Name",
            "Player 2 Name",
            "Player 3 Name",
            "Player 4 Name",
            "Player 5 Name",
            "Player 6 Name",
        ]

        def has_key_variant(base: str) -> bool:
            return any((k == base or k.startswith(base + "__")) for k in keys)

        # SmartSheet export:
        smart_required = ["Player Name"] + [f"Professional {i}" for i in range(1, 7)]

        if all((c in keys) for c in template_required):
            return True, None
        if all(has_key_variant(c) for c in smart_required):
            return True, None

        # Produce a readable error from the SmartSheet expected keys.
        missing = [c for c in smart_required if not has_key_variant(c)]
        if missing:
            return False, f"Missing required columns for SmartSheet export: {', '.join(missing)}"
        return False, "Unrecognized entries CSV format (missing required columns)"
    
    def validate_rebuys_columns(self, rows: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        Validate that rebuys CSV has required columns.
        
        Returns:
            (is_valid, error_message)
        """
        if not rows:
            return False, "File is empty"
        
        # Rebuy type is no longer required; it is inferred from replace pairs in the SmartSheet export.
        required_columns = [
            "Participant Name",
            "Original Player Name",
            "Rebuy Player Name",
        ]

        first_row = rows[0]
        missing_columns = [col for col in required_columns if col not in first_row]

        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        return True, None
    
    def import_entries(
        self,
        rows: List[Dict[str, str]],
        tournament_id: int,
        applied_suggestions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Import entries from parsed CSV rows.
        
        Args:
            rows: Parsed CSV rows
            tournament_id: Tournament ID to associate entries with
            applied_suggestions: Optional list of {"row": int, "column": str, "player_id": str}
                to use for that cell instead of matching the name (from validate "Did you mean?" approval).
        
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
        # Build lookup (row, column) -> player_id for applied typo corrections
        correction_lookup: Dict[Tuple[int, str], str] = {}
        if applied_suggestions:
            for s in applied_suggestions:
                r = s.get("row")
                c = s.get("column")
                pid = s.get("player_id")
                if r is not None and c and pid:
                    correction_lookup[(int(r), str(c).strip())] = str(pid)

        # Support both template and SmartSheet entries headers.
        first_row = rows[0]
        keys = set(first_row.keys())

        def has_key_variant(base: str) -> bool:
            return any((k == base or k.startswith(base + "__")) for k in keys)

        participant_key = "Participant Name" if has_key_variant("Participant Name") else "Player Name"
        player_header_keys = []
        for i in range(1, 7):
            template_key = f"Player {i} Name"
            smart_key = f"Professional {i}"
            if has_key_variant(template_key):
                k = next(k for k in keys if k == template_key or k.startswith(template_key + "__"))
                player_header_keys.append(k)
            else:
                k = next(k for k in keys if k == smart_key or k.startswith(smart_key + "__"))
                player_header_keys.append(k)
        
        results = {
            "success": True,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        for row_num, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            try:
                participant_name = (row.get(participant_key, "") or "").strip()
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
                
                # Match player names to IDs (use applied_suggestions when provided)
                player_ids = []
                player_errors = []
                
                for i in range(1, 7):
                    col = f"Player {i} Name"
                    actual_header_key = player_header_keys[i - 1]
                    player_name = (row.get(actual_header_key, "") or "").strip()
                    if not player_name:
                        player_errors.append(f"Player {i} Name is required")
                        continue
                    player_id = correction_lookup.get((row_num, col))
                    if not player_id:
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
        tournament_id: int,
        applied_suggestions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Import rebuys from parsed CSV rows.
        
        Args:
            rows: Parsed CSV rows
            tournament_id: Tournament ID
            applied_suggestions: Optional list of {"row": int, "column": str, "player_id": str}
                for "Original Player Name" or "Rebuy Player Name" spelling corrections.
        
        Returns:
            Dictionary with import results
        """
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            return {"success": False, "error": f"Tournament {tournament_id} not found"}

        header_keys = getattr(self, "_parsed_header_keys", []) or []
        pro6_key = next((k for k in header_keys if k == "Professional 6" or k.startswith("Professional 6__")), None)
        is_smart_sheet_rebuys = bool(pro6_key)

        correction_lookup: Dict[Tuple[int, str], str] = {}
        if applied_suggestions:
            for s in applied_suggestions:
                r, c, pid = s.get("row"), s.get("column"), s.get("player_id")
                if r is not None and c and pid:
                    correction_lookup[(int(r), str(c).strip())] = str(pid)

        results = {"success": True, "imported": 0, "skipped": 0, "errors": []}

        if is_smart_sheet_rebuys:
            first_row = rows[0] if rows else {}
            keys = set(first_row.keys())

            def has_key_variant(base: str) -> bool:
                return any((k == base or k.startswith(base + "__")) for k in keys)

            participant_key = "Participant Name" if has_key_variant("Participant Name") else "Player Name"
            pro6_idx = header_keys.index(pro6_key)
            replace_start_idx = pro6_idx + 1
            replace_pairs: List[Tuple[str, str]] = []
            for pair_idx in range(6):
                a = replace_start_idx + pair_idx * 2
                b = a + 1
                if b >= len(header_keys):
                    break
                replace_pairs.append((header_keys[a], header_keys[b]))

            if not replace_pairs:
                return {"success": False, "error": "Could not locate replace pairs in SmartSheet rebuy export."}

            for row_num, row in enumerate(rows, start=2):
                try:
                    participant_name = (row.get(participant_key) or "").strip()
                    if not participant_name:
                        results["errors"].append({"row": row_num, "error": "Participant Name is required"})
                        results["skipped"] += 1
                        continue

                    participant = self.db.query(Participant).filter(Participant.name == participant_name).first()
                    if not participant:
                        results["errors"].append({
                            "row": row_num,
                            "error": f"Participant '{participant_name}' not found. Import entries first."
                        })
                        results["skipped"] += 1
                        continue

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

                    player_positions = [
                        entry.player1_id, entry.player2_id, entry.player3_id,
                        entry.player4_id, entry.player5_id, entry.player6_id
                    ]

                    if entry.rebuy_player_ids is None:
                        entry.rebuy_player_ids = []
                    if entry.rebuy_original_player_ids is None:
                        entry.rebuy_original_player_ids = []

                    any_imported_this_row = False
                    for pair_idx, (orig_key, with_key) in enumerate(replace_pairs):
                        orig_name = (row.get(orig_key) or "").strip()
                        with_name = (row.get(with_key) or "").strip()

                        if not orig_name and not with_name:
                            continue

                        if not orig_name:
                            results["errors"].append({
                                "row": row_num,
                                "participant": participant_name,
                                "error": f"Missing Replace Original for replace pair {pair_idx + 1}"
                            })
                            continue

                        orig_col_identifier = f"Replace Original {pair_idx + 1}"
                        with_col_identifier = f"Replace With {pair_idx + 1}"

                        original_player_id = correction_lookup.get((row_num, orig_col_identifier))
                        if not original_player_id:
                            original_player_id = self.match_player_name(orig_name, tournament_id)

                        if not original_player_id or original_player_id not in player_positions:
                            results["errors"].append({
                                "row": row_num,
                                "participant": participant_name,
                                "error": f"Original player '{orig_name}' not found in entry"
                            })
                            continue

                        replacement_player_id = correction_lookup.get((row_num, with_col_identifier))
                        if not replacement_player_id:
                            replacement_player_id = self.match_player_name(with_name, tournament_id)

                        if not replacement_player_id:
                            results["errors"].append({
                                "row": row_num,
                                "participant": participant_name,
                                "error": f"Rebuy player '{with_name}' not found"
                            })
                            continue

                        if original_player_id in entry.rebuy_original_player_ids:
                            continue

                        entry.rebuy_original_player_ids.append(original_player_id)
                        entry.rebuy_player_ids.append(replacement_player_id)

                        any_imported_this_row = True

                    if any_imported_this_row:
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(entry, "rebuy_original_player_ids")
                        flag_modified(entry, "rebuy_player_ids")
                        results["imported"] += 1
                    else:
                        results["skipped"] += 1

                except Exception as e:
                    results["errors"].append({"row": row_num, "error": f"Unexpected error: {str(e)}"})
                    results["skipped"] += 1

            self.db.commit()
            return results

        # Normalized legacy mode (Participant Name, Original Player Name, Rebuy Player Name)
        is_valid, error = self.validate_rebuys_columns(rows)
        if not is_valid:
            return {"success": False, "error": error}

        for row_num, row in enumerate(rows, start=2):
            try:
                participant_name = (row.get("Participant Name") or "").strip()
                original_player_name = (row.get("Original Player Name") or "").strip()
                rebuy_player_name = (row.get("Rebuy Player Name") or "").strip()

                if not participant_name:
                    results["errors"].append({"row": row_num, "error": "Participant Name is required"})
                    results["skipped"] += 1
                    continue
                if not original_player_name:
                    results["errors"].append({"row": row_num, "error": "Original Player Name is required"})
                    results["skipped"] += 1
                    continue
                if not rebuy_player_name:
                    results["errors"].append({"row": row_num, "error": "Rebuy Player Name is required"})
                    results["skipped"] += 1
                    continue

                participant = self.db.query(Participant).filter(Participant.name == participant_name).first()
                if not participant:
                    results["errors"].append({
                        "row": row_num,
                        "error": f"Participant '{participant_name}' not found. Import entries first."
                    })
                    results["skipped"] += 1
                    continue

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

                player_positions = [
                    entry.player1_id, entry.player2_id, entry.player3_id,
                    entry.player4_id, entry.player5_id, entry.player6_id
                ]

                original_player_id = correction_lookup.get((row_num, "Original Player Name"))
                if not original_player_id:
                    original_player_id = self.match_player_name(original_player_name, tournament_id)

                if not original_player_id or original_player_id not in player_positions:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Original player '{original_player_name}' not found in entry"
                    })
                    results["skipped"] += 1
                    continue

                rebuy_player_id = correction_lookup.get((row_num, "Rebuy Player Name"))
                if not rebuy_player_id:
                    rebuy_player_id = self.match_player_name(rebuy_player_name, tournament_id)

                if not rebuy_player_id:
                    results["errors"].append({
                        "row": row_num,
                        "participant": participant_name,
                        "error": f"Rebuy player '{rebuy_player_name}' not found"
                    })
                    results["skipped"] += 1
                    continue

                if entry.rebuy_player_ids is None:
                    entry.rebuy_player_ids = []
                if entry.rebuy_original_player_ids is None:
                    entry.rebuy_original_player_ids = []

                if original_player_id in entry.rebuy_original_player_ids:
                    results["skipped"] += 1
                    continue

                entry.rebuy_original_player_ids.append(original_player_id)
                entry.rebuy_player_ids.append(rebuy_player_id)

                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(entry, "rebuy_original_player_ids")
                flag_modified(entry, "rebuy_player_ids")

                results["imported"] += 1

            except Exception as e:
                results["errors"].append({"row": row_num, "error": f"Unexpected error: {str(e)}"})
                results["skipped"] += 1

        self.db.commit()
        return results
