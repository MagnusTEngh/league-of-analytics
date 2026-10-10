"""Database utility functions for League of Analytics.

This module contains reusable query functions for common operations
on the DuckDB database.
"""

import duckdb
from typing import List, Optional


def get_matches_for_account(db_path: str, puuid: str) -> List[str]:
    """
    Get all match IDs for a specific account (PUUID).
    
    Args:
        db_path: Path to the duckdb database
        puuid: Player UUID to filter by
        
    Returns:
        List of match IDs where the account participated
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        # Query matches table for games where this PUUID appears
        # This assumes match data contains participant information
        query = """
            SELECT match_id
            FROM matches
            WHERE json_contains(data->'info'->'participants', ?)
        """
        result = con.execute(query, (puuid,)).fetchall()
        return [row[0] for row in result]
    finally:
        con.close()


def get_matches_by_queue(db_path: str, queue_id: int) -> List[str]:
    """
    Get all match IDs for a specific queue type.
    
    Args:
        db_path: Path to the duckdb database
        queue_id: Queue ID to filter by
        
    Returns:
        List of match IDs for the specified queue
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT match_id
            FROM matches
            WHERE json_extract_string(data->'info', '$.queueId') = ?
        """
        result = con.execute(query, (str(queue_id),)).fetchall()
        return [row[0] for row in result]
    finally:
        con.close()


def get_match_count_by_queue(db_path: str) -> dict:
    """
    Get count of matches by queue type.
    
    Args:
        db_path: Path to the duckdb database
        
    Returns:
        Dictionary mapping queue ID to match count
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                json_extract_string(data->'info', '$.queueId') as queue_id,
                COUNT(*) as match_count
            FROM matches
            GROUP BY queue_id
        """
        result = con.execute(query).fetchall()
        return {row[0]: row[1] for row in result}
    finally:
        con.close()


def get_total_matches(db_path: str) -> int:
    """
    Get total number of matches in the database.
    
    Args:
        db_path: Path to the duckdb database
        
    Returns:
        Total count of matches
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        result = con.execute("SELECT COUNT(*) FROM matches").fetchone()
        return result[0] if result else 0
    finally:
        con.close()


def get_champion_stats_for_account(db_path: str, puuid: str) -> dict:
    """
    Get champion statistics for a specific account.
    
    Args:
        db_path: Path to the duckdb database
        puuid: Player UUID to filter by
        
    Returns:
        Dictionary with champion stats (champion_id -> {games, wins, losses})
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT 
                json_extract_string(p, '$.championId') as champion_id,
                COUNT(*) as games,
                SUM(CASE WHEN json_extract_boolean(p, '$.win') THEN 1 ELSE 0 END) as wins
            FROM matches, 
                UNNEST(json_extract_array(data->'info'->'participants', '$')) as p
            WHERE json_contains(p, ?)
            GROUP BY champion_id
        """
        result = con.execute(query, (puuid,)).fetchall()
        return {
            row[0]: {"games": row[1], "wins": row[2], "losses": row[1] - row[2]}
            for row in result
        }
    finally:
        con.close()


def get_winrate_by_champion(db_path: str, puuid: str) -> dict:
    """
    Get winrate by champion for a specific account.
    
    Args:
        db_path: Path to the duckdb database
        puuid: Player UUID to filter by
        
    Returns:
        Dictionary mapping champion_id to winrate (0-1)
    """
    stats = get_champion_stats_for_account(db_path, puuid)
    return {champ: data["wins"] / data["games"] if data["games"] > 0 else 0 
            for champ, data in stats.items()}


def get_recent_matches(db_path: str, limit: int = 10) -> List[str]:
    """
    Get most recent matches by game creation time.
    
    Args:
        db_path: Path to the duckdb database
        limit: Maximum number of matches to return
        
    Returns:
        List of match IDs sorted by recency (most recent first)
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT match_id
            FROM matches
            ORDER BY json_extract_int(data->'info', '$.gameCreation') DESC
            LIMIT ?
        """
        result = con.execute(query, (limit,)).fetchall()
        return [row[0] for row in result]
    finally:
        con.close()


def get_match_by_id(db_path: str, match_id: str) -> Optional[dict]:
    """
    Get full match data for a specific match ID.
    
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


def get_timeline_by_id(db_path: str, match_id: str) -> Optional[dict]:
    """
    Get timeline data for a specific match ID.
    
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
