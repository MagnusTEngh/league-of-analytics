"""Build a duckdb database from downloaded match/timeline JSON files.

Two tables are produced, each with the raw API response kept as a single
VARIANT column - no unpacking here, that's left to the Analytics app's queries.
"""

import json
import os
import re
import logging

import duckdb

from data.api.utils import list_compressed_files, read_compressed_json

logger = logging.getLogger(__name__)

MATCH_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)$")
TIMELINE_FILENAME_RE = re.compile(r"^(?P<region>[a-z]+)_(?P<match_id>[A-Z0-9_]+)_timeline$")


def list_existing_matches(match_dir: str = "data/match") -> list[str]:
    """List .json.zst match files already downloaded."""
    return list_compressed_files(match_dir)


def list_existing_timelines(timeline_dir: str = "data/timeline") -> list[str]:
    """List .json.zst timeline files already downloaded."""
    return list_compressed_files(timeline_dir)


def _stem(filepath: str) -> str:
    """Filename without directory or .json.zst extension."""
    return os.path.basename(filepath).removesuffix(".json.zst")


def _load_matches(con: duckdb.DuckDBPyConnection, match_dir: str) -> None:
    """Load match data into the matches table."""
    con.execute("""
        CREATE OR REPLACE TABLE matches (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data VARIANT
        )
    """)

    rows = []
    for filepath in list_existing_matches(match_dir):
        m = MATCH_FILENAME_RE.match(_stem(filepath))
        if not m:
            logger.warning("Skipping unrecognised match filename: %s", filepath)
            continue

        data = read_compressed_json(filepath)
        if data is None:
            continue

        rows.append((m["match_id"], m["region"], data))

    if rows:
        con.executemany(
            "INSERT INTO matches VALUES (?, ?, ?)",
            [(match_id, region, json.dumps(data)) for match_id, region, data in rows],
        )
        logger.info("Loaded %d matches", len(rows))


def _load_timelines(con: duckdb.DuckDBPyConnection, timeline_dir: str) -> None:
    """Load timeline data into the timelines table."""
    con.execute("""
        CREATE OR REPLACE TABLE timelines (
            match_id VARCHAR PRIMARY KEY,
            region VARCHAR,
            data VARIANT
        )
    """)

    rows = []
    for filepath in list_existing_timelines(timeline_dir):
        m = TIMELINE_FILENAME_RE.match(_stem(filepath))
        if not m:
            logger.warning("Skipping unrecognised timeline filename: %s", filepath)
            continue

        data = read_compressed_json(filepath)
        if data is None:
            continue

        rows.append((m["match_id"], m["region"], data))

    if rows:
        con.executemany(
            "INSERT INTO timelines VALUES (?, ?, ?)",
            [(match_id, region, json.dumps(data)) for match_id, region, data in rows],
        )
        logger.info("Loaded %d timelines", len(rows))


def make_duckdb(
    db_path: str = "data/league.duckdb",
    match_dir: str = "data/match",
    timeline_dir: str = "data/timeline",
) -> str:
    """
    Build (or rebuild) a duckdb database with `matches` and `timelines`
    tables, one row per downloaded file, data kept as VARIANT type.

    Returns:
        Path to the duckdb database file.
    """
    con = duckdb.connect(db_path)
    try:
        _load_matches(con, match_dir)
        _load_timelines(con, timeline_dir)
    finally:
        con.close()

    logger.info("Database written to %s", db_path)
    return db_path


if __name__ == "__main__":
    make_duckdb()
