"""Database module for League of Analytics.

This module provides functions for building and querying a DuckDB database
from the stored API response files.
"""

import os
import re
import json
import zstandard as zstd
from typing import Optional, List, Dict, Any

import duckdb


# Regex patterns for parsing filenames
MATCH_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)$")
TIMELINE_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)$")
ACCOUNT_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<puuid>[A-Za-z0-9_-]+)$")


def _get_storage_path() -> str:
    """Get the base storage path for data files."""
    return "data"


def list_compressed_files(subdir: str) -> List[str]:
    """
    List all .json.zst files in a subdirectory.
    
    Args:
        subdir: Subdirectory under storage path
        
    Returns:
        List of file paths
    """
    storage_path = _get_storage_path()
    data_dir = os.path.join(storage_path, subdir)
    
    if not os.path.exists(data_dir):
        return []
    
    files = []
    for f in os.listdir(data_dir):
        if f.endswith('.json.zst'):
            files.append(os.path.join(data_dir, f))
    return files


def read_compressed_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Read a compressed JSON file.
    
    Args:
        filepath: Path to the .json.zst file
        
    Returns:
        Parsed JSON data, or None if failed
    """
    try:
        dctx = zstd.ZstdDecompressor()
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
        json_data = dctx.decompress(compressed_data)
        return json.loads(json_data)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def _stem(filepath: str) -> str:
    """Filename without directory or .json.zst extension."""
    return os.path.basename(filepath).removesuffix(".json.zst")


def _load_matches(con: duckdb.DuckDBPyConnection, match_dir: str = "match_v5") -> None:
    """Load match data into the matches table."""
    con.execute("""
        CREATE OR REPLACE TABLE matches (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data VARIANT
        )
    """)
    
    rows = []
    storage_path = _get_storage_path()
    full_match_dir = os.path.join(storage_path, match_dir)
    
    for filepath in list_compressed_files(match_dir):
        m = MATCH_FILENAME_RE.match(_stem(filepath))
        if not m:
            print(f"  Skipping unrecognised match filename: {filepath}")
            continue
        
        data = read_compressed_json(filepath)
        if data is None:
            continue
        
        rows.append((m["match_id"], m["region"], data))
    
    if rows:
        con.executemany(
            "INSERT INTO matches VALUES (?, ?, ?)",
            [(match_id, region, data) for match_id, region, data in rows],
        )
        print(f"  Loaded {len(rows)} matches")


def _load_timelines(con: duckdb.DuckDBPyConnection, timeline_dir: str = "timelines") -> None:
    """Load timeline data into the timelines table."""
    con.execute("""
        CREATE OR REPLACE TABLE timelines (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data VARIANT
        )
    """)
    
    rows = []
    for filepath in list_compressed_files(timeline_dir):
        m = TIMELINE_FILENAME_RE.match(_stem(filepath))
        if not m:
            print(f"  Skipping unrecognised timeline filename: {filepath}")
            continue
        
        data = read_compressed_json(filepath)
        if data is None:
            continue
        
        rows.append((m["match_id"], m["region"], data))
    
    if rows:
        con.executemany(
            "INSERT INTO timelines VALUES (?, ?, ?)",
            [(match_id, region, data) for match_id, region, data in rows],
        )
        print(f"  Loaded {len(rows)} timelines")


def _load_accounts(con: duckdb.DuckDBPyConnection, account_dir: str = "account") -> None:
    """Load account data into the accounts table."""
    con.execute("""
        CREATE OR REPLACE TABLE accounts (
            puuid VARCHAR PRIMARY KEY,
            region VARCHAR,
            data VARIANT
        )
    """)
    
    rows = []
    for filepath in list_compressed_files(account_dir):
        m = ACCOUNT_FILENAME_RE.match(_stem(filepath))
        if not m:
            print(f"  Skipping unrecognised account filename: {filepath}")
            continue
        
        data = read_compressed_json(filepath)
        if data is None:
            continue
        
        rows.append((m["puuid"], m["region"], data))
    
    if rows:
        con.executemany(
            "INSERT INTO accounts VALUES (?, ?, ?)",
            [(puuid, region, data) for puuid, region, data in rows],
        )
        print(f"  Loaded {len(rows)} accounts")


def make_duckdb(
    db_path: str = "data/league.duckdb",
    match_dir: str = "match_v5",
    timeline_dir: str = "timelines",
    account_dir: str = "account",
) -> str:
    """
    Build (or rebuild) a duckdb database with tables for each endpoint.
    
    One row per downloaded file, data kept as VARIANT type.
    
    Args:
        db_path: Path to the duckdb database file
        match_dir: Directory containing match files
        timeline_dir: Directory containing timeline files
        account_dir: Directory containing account files
        
    Returns:
        Path to the duckdb database file
    """
    # Ensure directories exist
    storage_path = _get_storage_path()
    os.makedirs(os.path.join(storage_path, match_dir), exist_ok=True)
    os.makedirs(os.path.join(storage_path, timeline_dir), exist_ok=True)
    os.makedirs(os.path.join(storage_path, account_dir), exist_ok=True)
    
    con = duckdb.connect(db_path)
    try:
        _load_matches(con, match_dir)
        _load_timelines(con, timeline_dir)
        _load_accounts(con, account_dir)
    finally:
        con.close()
    
    print(f"Database written to {db_path}")
    return db_path


def get_connection(db_path: str = "data/league.duckdb") -> duckdb.DuckDBPyConnection:
    """
    Get a read-only connection to the DuckDB database.
    
    Args:
        db_path: Path to the duckdb database file
        
    Returns:
        DuckDB connection object
    """
    return duckdb.connect(db_path, read_only=True)


if __name__ == "__main__":
    make_duckdb()
