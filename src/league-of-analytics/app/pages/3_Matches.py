"""Matches page for League of Analytics.

This page displays all data associated with a selected match ID.
"""

import streamlit as st

st.title("Matches")
st.write("This is the Matches page.")

# Display selected account from session state
if "selected_account" in st.session_state:
    st.write(f"Selected Account: **{st.session_state.selected_account}**")
else:
    st.write("No account selected. Please select an account from the sidebar.")

st.write("\nHere you can see your match history and detailed match analysis.")

# Placeholder for actual content
st.subheader("Match History")
st.write("- List of recent matches")
st.write("- Match selector for detailed view")
st.write("- Full match data display")
