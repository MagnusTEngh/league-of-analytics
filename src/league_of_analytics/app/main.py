"""App entrypoint: shared sidebar (player selection) and page navigation."""

import streamlit as st

st.set_page_config(page_title="League of Analytics", layout="wide")

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