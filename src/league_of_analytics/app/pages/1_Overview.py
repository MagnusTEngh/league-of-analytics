"""Overview page for League of Analytics.

This page displays key stats such as:
- Amount of games played by queue and in total
- Winrates
- Games over time by patch
- Fun stats like high scores
"""

import streamlit as st

st.title("Overview")
st.write("This is the Overview page.")

# Display selected account from session state
if "selected_account" in st.session_state:
    st.write(f"Selected Account: **{st.session_state.selected_account}**")
else:
    st.write("No account selected. Please select an account from the sidebar.")

st.write("\nHere you can see an overview of your League of Legends analytics.")

# Placeholder for actual content
st.subheader("Key Statistics")
st.write("- Total games played")
st.write("- Win rate by queue")
st.write("- Games over time")
st.write("- High scores collection")
