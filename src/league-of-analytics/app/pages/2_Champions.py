"""Champions page for League of Analytics.

This page displays:
- An overview of which Champions the player favors
- A selector to pick a specific champion for detailed stats
- Champion splash art when a champion is selected
"""

import streamlit as st

st.title("Champions")
st.write("This is the Champions page.")

# Display selected account from session state
if "selected_account" in st.session_state:
    st.write(f"Selected Account: **{st.session_state.selected_account}**")
else:
    st.write("No account selected. Please select an account from the sidebar.")

st.write("\nHere you can see champion statistics and performance.")

# Placeholder for actual content
st.subheader("Champion Overview")
st.write("- Most played champions")
st.write("- Win rate by champion")
st.write("- Champion selector for detailed stats")
st.write("- Champion splash art display")
