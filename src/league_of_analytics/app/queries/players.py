"""Player queries for the app, using the DuckDB Python API on the read-only database."""

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("data_storage_path", "data")) / "league.duckdb"

# One row per game for the player: match_id, queue_id, game_version and the participant JSON `p`.
PLAYER_CTE = r"""
WITH player AS (
    SELECT match_id, queue_id, game_version, p
    FROM (
        SELECT match_id,
               data->>'$.info.queueId' AS queue_id,
               data->>'$.info.gameVersion' AS game_version,
               unnest(from_json(data->'$.info.participants', '["JSON"]')) AS p
        FROM matches
    )
    WHERE lower(p->>'$.riotIdGameName') = lower($name)
      AND lower(p->>'$.riotIdTagline') = lower($tag)
)
"""


@st.cache_resource
def connect() -> duckdb.DuckDBPyConnection:
    """Shared read-only connection. Use `.cursor()` per query (Streamlit is multi-threaded)."""
    return duckdb.connect(str(DB_PATH), read_only=True)


def _player_query(select_sql: str, name: str, tag: str) -> pd.DataFrame:
    with connect().cursor() as cur:
        return cur.execute(PLAYER_CTE + select_sql, {"name": name, "tag": tag}).df()


def selected_player() -> tuple[str, str]:
    """Return (name, tag) from the sidebar Riot ID, or stop the page with a hint."""
    riot_id = st.session_state.get("riot_id", "")  # set by the sidebar in app/main.py
    if "#" not in riot_id:
        st.info("Enter a Riot ID like `name#tag` in the sidebar.")
        st.stop()
    if not DB_PATH.exists():
        st.warning(
            f"Database not found at `{DB_PATH}`. "
            "Run `uv run src/league_of_analytics/database/main.py` first."
        )
        st.stop()
    name, tag = riot_id.rsplit("#", 1)
    return name.strip(), tag.strip()


@st.cache_data
def player_games(name: str, tag: str) -> pd.DataFrame:
    """One row per game with the stats shown on the Home page."""
    return _player_query(
        r"""
        SELECT match_id AS game_id,
               queue_id::INT AS queue_id,
               regexp_extract(game_version, '^(\d+\.\d+)', 1) AS patch,
               (p->>'$.win')::BOOLEAN::INT AS win,
               p->>'$.championName' AS champion,
               (p->>'$.kills')::INT AS kills,
               (p->>'$.deaths')::INT AS deaths,
               (p->>'$.assists')::INT AS assists,
               (p->>'$.wardsPlaced')::INT AS wards_placed,
               TRY_CAST(p->>'$.challenges.skillshotsDodged' AS INT) AS dodged_skillshots,
               TRY_CAST(p->>'$.enemyMissingPings' AS INT) AS missing_pings
        FROM player
        """,
        name,
        tag,
    )


def _int_expr(field: str) -> str:
    """SQL turning a participant field (number or true/false) into an integer."""
    if not field.isidentifier():
        raise ValueError(f"Invalid field name: {field}")
    raw = f"lower(p->>'$.{field}')"
    return f"CASE {raw} WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE TRY_CAST({raw} AS INT) END"


@st.cache_data
def player_features(name: str, tag: str, features: tuple[str, ...]) -> pd.DataFrame:
    """Win flag plus the chosen participant fields as integers, one row per game."""
    cols = ", ".join(f"{_int_expr(f)} AS {f}" for f in features)
    return _player_query(
        f"SELECT (p->>'$.win')::BOOLEAN::INT AS win, {cols} FROM player", name, tag
    )