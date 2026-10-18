"""Home page: overview stats for a single player, selected by Riot ID (name#tag)."""

import pandas as pd
import plotly.express as px
import streamlit as st

from league_of_analytics.app.queries.players import player_games, selected_player

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


def sorted_patches(patches) -> list[str]:
    return sorted(patches, key=lambda v: tuple(int(x) for x in v.split(".")))


def champion_pie(games: pd.DataFrame, share: float = 0.8):
    """Pie of the most played champions covering `share` of games, rest as Others."""
    counts = games["champion"].value_counts()
    top = counts[counts.cumsum() <= counts.sum() * share]
    others = counts.sum() - top.sum()
    if others:
        top = pd.concat([top, pd.Series({"Others": others})])
    fig = px.pie(names=top.index, values=top.values, hole=0.3)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


st.title("Welcome to the landing page!")

name, tag = selected_player()
games = player_games(name, tag)
if games.empty:
    st.warning(f"No games found for {name}#{tag}.")
    st.stop()

games = games.assign(
    queue=games["queue_id"].map(QUEUE_NAMES).fillna(games["queue_id"].astype(str))
)
queue = st.selectbox("Queue", ["All", *sorted(games["queue"].unique())])
if queue != "All":
    games = games[games["queue"] == queue]

left, right = st.columns(2)

with left:
    st.subheader("Games by queue")
    per_queue = games.groupby("queue", as_index=False).agg(games=("game_id", "nunique"))
    st.plotly_chart(px.pie(per_queue, values="games", names="queue"), width="stretch")

with right:
    st.subheader("Highscores (best single game)")
    best = games[list(HIGHSCORES.values())].max().fillna(0)
    items = list(HIGHSCORES.items())
    for row in (items[:3], items[3:]):
        for col, (label, key) in zip(st.columns(3), row):
            col.metric(label, int(best[key]))

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Winrate by queue and patch")
    per_patch = games.groupby(["queue", "patch"], as_index=False).agg(
        winrate=("win", "mean"), games=("game_id", "nunique")
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
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Champions played")
    st.plotly_chart(champion_pie(games), width="stretch")