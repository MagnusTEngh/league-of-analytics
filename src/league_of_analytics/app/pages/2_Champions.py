"""Champion page: select a champion and show its splash art."""

import requests
import streamlit as st

DDRAGON = "https://ddragon.leagueoflegends.com"


@st.cache_data(ttl=24 * 3600)
def champion_names() -> list[str]:
    """Champion ids from the latest Data Dragon release."""
    version = requests.get(f"{DDRAGON}/api/versions.json", timeout=10).json()[0]
    data = requests.get(
        f"{DDRAGON}/cdn/{version}/data/en_US/champion.json", timeout=10
    ).json()["data"]
    return sorted(data)


def splash_url(champion: str) -> str:
    return f"{DDRAGON}/cdn/img/champion/splash/{champion}_0.jpg"


st.title("Champion")

champion = st.selectbox("Select champion", champion_names(), index=None)
if champion:
    st.image(splash_url(champion), caption=champion)