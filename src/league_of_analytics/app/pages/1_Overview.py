"""Home page: overview stats for a single player, selected by Riot ID (name#tag)."""

import ibis
import plotly.express as px
import streamlit as st
from ibis import _
from queries import player_rows, selected_player

QUEUE_NAMES = {
    400: "Normal Draft",
    420: "Ranked Solo/Duo",
    430: "Normal Blind",
    440: "Ranked Flex",
    450: "ARAM",
    700: "Clash",
}
HIGHSCORES = {
    "Kills": "kills",
    "Deaths": "deaths",
    "Assists": "assists",
    "Wards placed": "wards_placed",
    "Dodged skillshots": "dodged_skillshots",
    "Missing pings": "missing_pings",
}


def player_games(name: str, tag: str) -> ibis.Table:
    """One row per game for the player, read lazily from the .json.zst match files."""
    games = player_rows(name, tag).select(
        "game_id",
        "queue_id",
        patch=_.game_version.re_extract(r"^(\d+\.\d+)", 1),
        win=_.p.win.cast("int"),
        champion=_.p.championName,
        kills=_.p.kills,
        deaths=_.p.deaths,
        assists=_.p.assists,
        wards_placed=_.p.wardsPlaced,
        dodged_skillshots=_.p.challenges.skillshotsDodged,
        missing_pings=_.p.enemyMissingPings,
    )
    queues = ibis.memtable(
        [{"queue_id": k, "queue": v} for k, v in QUEUE_NAMES.items()]
    )
    return games.left_join(queues, "queue_id").mutate(
        queue=ibis.coalesce(_.queue, _.queue_id.cast("string"))
    )


def sorted_patches(patches) -> list[str]:
    return sorted(patches, key=lambda v: tuple(int(x) for x in v.split(".")))


def champion_pie(games: ibis.Table, share: float = 0.8):
    """Pie of the most played champions covering `share` of games, rest as Others."""
    counts = (
        games.group_by("champion")
        .agg(count=_.count())
        .order_by(_["count"].desc())
        .execute()
    )
    is_top = counts["count"].cumsum() <= counts["count"].sum() * share
    others = counts.loc[~is_top, "count"].sum()
    top = counts[is_top].copy()
    if others:
        top.loc[len(top)] = ["Others", others]
    fig = px.pie(top, names="champion", values="count", hole=0.3)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


st.title("Welcome to the landing page!")

name, tag = selected_player()
games = player_games(name, tag)

queues = sorted(games.queue.unique().to_pyarrow().to_pylist())
if not queues:
    st.warning(f"No games found for {name}#{tag}.")
    st.stop()

queue = st.selectbox("Queue", ["All", *queues])
if queue != "All":
    games = games.filter(_.queue == queue)

left, right = st.columns(2)

with left:
    st.subheader("Games by queue")
    per_queue = games.group_by("queue").agg(games=_.game_id.nunique()).execute()
    st.plotly_chart(px.pie(per_queue, values="games", names="queue"), use_container_width=True)

with right:
    st.subheader("Highscores (best single game)")
    best = games.aggregate(**{col: _[col].max() for col in HIGHSCORES.values()}).to_pyarrow().to_pylist()[0]
    items = list(HIGHSCORES.items())
    for row in (items[:3], items[3:]):
        for col, (label, key) in zip(st.columns(3), row):
            col.metric(label, best[key])

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Winrate by queue and patch")
    per_patch = (
        games.group_by("queue", "patch")
        .agg(winrate=_.win.mean(), games=_.game_id.nunique())
        .execute()
    )
    fig = px.line(
        per_patch,
        x="patch",
        y="winrate",
        color="queue",
        hover_data=["games"],
        category_orders={"patch": sorted_patches(per_patch["patch"].unique())},
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Champions played")
    st.plotly_chart(champion_pie(games), use_container_width=True)