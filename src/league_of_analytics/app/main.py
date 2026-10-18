"""App entrypoint: shared sidebar (player selection), dark chart defaults and page navigation."""

import plotly.express as px
import plotly.io as pio
import streamlit as st

st.set_page_config(page_title="League of Analytics", layout="wide")

# Dark Plotly defaults: transparent background so charts blend into the charcoal page.
dark = pio.templates["plotly_dark"]
dark.layout.paper_bgcolor = "rgba(0,0,0,0)"
dark.layout.plot_bgcolor = "rgba(0,0,0,0)"
pio.templates.default = "plotly_dark"
px.defaults.color_discrete_sequence = [
    "#8B5CF6", "#C4B5FD", "#A78BFA", "#6D28D9",
    "#DDD6FE", "#5B21B6", "#9CA3AF", "#4C1D95",
]  # violet and lavender tones plus gray

# Runs on every page, so the selected player is shared via st.session_state["riot_id"].
st.sidebar.text_input("Riot ID", key="riot_id", placeholder="name#tag")

navigation = st.navigation(
    [
        st.Page("pages/1_Overview.py", title="Home", default=True),
        st.Page("pages/2_Champions.py", title="Champions"),
        st.Page("pages/3_Analytics.py", title="Analytics"),
    ]
)
navigation.run()