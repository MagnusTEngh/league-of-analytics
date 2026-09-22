"""Build a duckdb database from downloaded match/timeline JSON files.

Two tables are produced, each with the raw API response kept as a single
JSON column — no unpacking here, that's left to the Analytics app's queries.
"""

import os
import re
import duckdb

from data.api.utils import list_compressed_files, read_compressed_json

MATCH_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)$")
TIMELINE_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)_timeline$")


def list_existing_matches(match_dir: str = "data/match") -> list:
    """List .json.zst match files already downloaded."""
    return list_compressed_files(match_dir)


def list_existing_timelines(timeline_dir: str = "data/timeline") -> list:
    """List .json.zst timeline files already downloaded."""
    return list_compressed_files(timeline_dir)


def _stem(filepath: str) -> str:
    """Filename without directory or .json.zst extension."""
    return os.path.basename(filepath).removesuffix(".json.zst")


def _load_matches(con: duckdb.DuckDBPyConnection, match_dir: str) -> None:
    con.execute("""
        CREATE OR REPLACE TABLE matches (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data JSON
        )
    """)

    rows = []
    for filepath in list_existing_matches(match_dir):
        m = MATCH_FILENAME_RE.match(_stem(filepath))
        if not m:
            print(f"  Skipping unrecognised match filename: {filepath}")
            continue

        data = read_compressed_json(filepath)
        if data is None:
            continue

        rows.append((m["match_id"], m["region"], data))

    con.executemany(
        "INSERT INTO matches VALUES (?, ?, ?)",
        [(match_id, region, __import__("json").dumps(data)) for match_id, region, data in rows],
    )
    print(f"  Loaded {len(rows)} matches")


def _load_timelines(con: duckdb.DuckDBPyConnection, timeline_dir: str) -> None:
    con.execute("""
        CREATE OR REPLACE TABLE timelines (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data JSON
        )
    """)

    rows = []
    for filepath in list_existing_timelines(timeline_dir):
        m = TIMELINE_FILENAME_RE.match(_stem(filepath))
        if not m:
            print(f"  Skipping unrecognised timeline filename: {filepath}")
            continue

        data = read_compressed_json(filepath)
        if data is None:
            continue

        rows.append((m["match_id"], m["region"], data))

    con.executemany(
        "INSERT INTO timelines VALUES (?, ?, ?)",
        [(match_id, region, __import__("json").dumps(data)) for match_id, region, data in rows],
    )
    print(f"  Loaded {len(rows)} timelines")


def make_duckdb(
    db_path: str = "data/league.duckdb",
    match_dir: str = "data/match",
    timeline_dir: str = "data/timeline",
) -> str:
    """
    Build (or rebuild) a duckdb database with `matches` and `timelines`
    tables, one row per downloaded file, data kept as nested JSON.

    Returns:
        Path to the duckdb database file.
    """
    con = duckdb.connect(db_path)
    try:
        _load_matches(con, match_dir)
        _load_timelines(con, timeline_dir)
    finally:
        con.close()

    print(f"Database written to {db_path}")
    return db_path


if __name__ == "__main__":
    make_duckdb()


