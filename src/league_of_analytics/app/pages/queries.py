"""Shared data access for app pages."""

from glob import glob

import ibis
import streamlit as st
from ibis import _

MATCH_GLOB = "data/match/*.json.zst"


@st.cache_resource
def connect():
    return ibis.duckdb.connect()


def player_rows(name: str, tag: str) -> ibis.Table:
    """One row per game for the player: game_id, queue_id, game_version and the participant struct `p`."""
    matches = connect().read_json(MATCH_GLOB, union_by_name=True)
    rows = matches.select(
        game_id=_.metadata.matchId,
        queue_id=_.info.queueId,
        game_version=_.info.gameVersion,
        p=_.info.participants.unnest(),
    )
    return rows.filter(
        _.p.riotIdGameName.lower() == name.lower(),
        _.p.riotIdTagline.lower() == tag.lower(),
    )


def selected_player() -> tuple[str, str]:
    """Return (name, tag) from the sidebar Riot ID, or stop the page with a hint."""
    riot_id = st.session_state.get("riot_id", "")  # set by the sidebar in app.py
    if "#" not in riot_id:
        st.info("Enter a Riot ID like `name#tag` in the sidebar.")
        st.stop()
    if not glob(MATCH_GLOB):
        st.warning("No match files found. Run `python -m data.fetch_league_matches` first.")
        st.stop()
    name, tag = riot_id.rsplit("#", 1)
    return name.strip(), tag.strip()