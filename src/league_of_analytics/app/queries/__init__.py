"""Queries module for League of Analytics app.

This module contains reusable query functions that can be shared between apps.
Functions are grouped by logical categories.

Common query categories:
- Account queries: Get account info, match history, etc.
- Champion queries: Get champion stats, mastery, etc.
- Match queries: Get match details, timeline, etc.
- Stats queries: Get aggregated statistics, win rates, etc.
"""

from typing import List, Dict, Optional
import duckdb


def get_account_info(db_path: str, account_id: str) -> Optional[Dict]:
    """
    Get account information from the database.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to look up
        
    Returns:
        Account data as dictionary, or None if not found
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT data
            FROM accounts
            WHERE puuid = ?
        """
        result = con.execute(query, (account_id,)).fetchone()
        return result[0] if result else None
    finally:
        con.close()


def get_account_matches(db_path: str, account_id: str) -> List[str]:
    """
    Get all match IDs for a specific account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        List of match IDs
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        # This query finds matches where the account's PUUID appears in participants
        query = """
            SELECT DISTINCT m.match_id
            FROM matches m
            JOIN (
                SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as participant
                FROM matches
            ) p
            WHERE json_contains(p.participant, ?)
        """
        result = con.execute(query, (account_id,)).fetchall()
        return [row[0] for row in result]
    finally:
        con.close()


def get_total_games(db_path: str, account_id: str) -> int:
    """
    Get total number of games played by an account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Total count of games
    """
    matches = get_account_matches(db_path, account_id)
    return len(matches)


def get_winrate(db_path: str, account_id: str) -> float:
    """
    Get overall winrate for an account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Winrate as float (0-1)
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN json_extract_boolean(p, '$.win') THEN 1 ELSE 0 END) as wins
            FROM matches m
            JOIN (
                SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
                FROM matches
            ) p
            WHERE json_contains(p.p, ?)
        """
        result = con.execute(query, (account_id,)).fetchone()
        if result and result[0] > 0:
            return result[1] / result[0]
        return 0.0
    finally:
        con.close()


def get_winrate_by_queue(db_path: str, account_id: str) -> Dict[str, float]:
    """
    Get winrate by queue type for an account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Dictionary mapping queue ID to winrate
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                json_extract_string(m.data->'info', '$.queueId') as queue_id,
                COUNT(*) as total,
                SUM(CASE WHEN json_extract_boolean(p, '$.win') THEN 1 ELSE 0 END) as wins
            FROM matches m
            JOIN (
                SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
                FROM matches
            ) p
            WHERE json_contains(p.p, ?)
            GROUP BY queue_id
        """
        result = con.execute(query, (account_id,)).fetchall()
        return {row[0]: row[2] / row[1] if row[1] > 0 else 0 for row in result}
    finally:
        con.close()


def get_champion_stats(db_path: str, account_id: str) -> Dict[str, Dict]:
    """
    Get champion statistics for an account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Dictionary mapping champion ID to stats dict with:
        - games: Total games played
        - wins: Number of wins
        - losses: Number of losses
        - winrate: Win rate (0-1)
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                json_extract_string(p, '$.championId') as champion_id,
                COUNT(*) as games,
                SUM(CASE WHEN json_extract_boolean(p, '$.win') THEN 1 ELSE 0 END) as wins
            FROM matches m
            JOIN (
                SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
                FROM matches
            ) p
            WHERE json_contains(p.p, ?)
            GROUP BY champion_id
        """
        result = con.execute(query, (account_id,)).fetchall()
        return {
            row[0]: {
                "games": row[1],
                "wins": row[2],
                "losses": row[1] - row[2],
                "winrate": row[2] / row[1] if row[1] > 0 else 0
            }
            for row in result
        }
    finally:
        con.close()


def get_games_by_patch(db_path: str, account_id: str) -> Dict[str, int]:
    """
    Get number of games played by patch version.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Dictionary mapping patch version to game count
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                json_extract_string(m.data->'info', '$.gameVersion') as patch,
                COUNT(*) as games
            FROM matches m
            JOIN (
                SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
                FROM matches
            ) p
            WHERE json_contains(p.p, ?)
            GROUP BY patch
            ORDER BY patch
        """
        result = con.execute(query, (account_id,)).fetchall()
        return {row[0]: row[1] for row in result}
    finally:
        con.close()


def get_high_scores(db_path: str, account_id: str) -> Dict[str, int]:
    """
    Get high scores for various stats for an account.
    
    Args:
        db_path: Path to the duckdb database
        account_id: Account ID (PUUID) to filter by
        
    Returns:
        Dictionary with high score values for:
        - kills
        - deaths
        - assists
        - wards_placed
        - dodged_skillshots
        - missing_pings
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        stats = {}
        
        # Query for each stat type
        for stat_name, json_path in [
            ("kills", "$.kills"),
            ("deaths", "$.deaths"),
            ("assists", "$.assists"),
            ("wards_placed", "$.wardsPlaced"),
        ]:
            query = f"""
                SELECT MAX(json_extract_int(p, '{json_path}')) as max_{stat_name}
                FROM matches m
                JOIN (
                    SELECT UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
                    FROM matches
                ) p
                WHERE json_contains(p.p, ?)
            """
            result = con.execute(query, (account_id,)).fetchone()
            stats[stat_name] = result[0] if result and result[0] else 0
        
        return stats
    finally:
        con.close()


def get_match_details(db_path: str, match_id: str) -> Optional[Dict]:
    """
    Get full details for a specific match.
    
    Args:
        db_path: Path to the duckdb database
        match_id: Match ID to retrieve
        
    Returns:
        Match data as dictionary, or None if not found
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT data
            FROM matches
            WHERE match_id = ?
        """
        result = con.execute(query, (match_id,)).fetchone()
        return result[0] if result else None
    finally:
        con.close()


def get_match_timeline(db_path: str, match_id: str) -> Optional[Dict]:
    """
    Get timeline data for a specific match.
    
    Args:
        db_path: Path to the duckdb database
        match_id: Match ID to retrieve
        
    Returns:
        Timeline data as dictionary, or None if not found
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT data
            FROM timelines
            WHERE match_id = ?
        """
        result = con.execute(query, (match_id,)).fetchone()
        return result[0] if result else None
    finally:
        con.close()
