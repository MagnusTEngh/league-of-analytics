import streamlit as st

st.title("Champions")
st.write("This is the Champions page.")

# Display selected account from session state
if "selected_account" in st.session_state:
    st.write(f"Selected Account: **{st.session_state.selected_account}**")
else:
    st.write("No account selected. Please select an account from the sidebar.")

st.write("\nHere you can see champion statistics and performance.")
