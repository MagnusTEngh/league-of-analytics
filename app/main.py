import streamlit as st

# Initialize session state for account selection
if "selected_account" not in st.session_state:
    st.session_state.selected_account = None

# Sidebar with account selector
with st.sidebar:
    st.title("League of Analytics")
    
    # Account selection dropdown
    account_options = [
        "account1#tag1",
        "account2#tag2", 
        "account3#tag3",
        "account4#tag4",
    ]
    
    selected_account = st.selectbox(
        "Select Account",
        options=account_options,
        index=0 if st.session_state.selected_account is None else account_options.index(st.session_state.selected_account) if st.session_state.selected_account in account_options else 0,
        key="account_selector"
    )
    
    # Update session state when selection changes
    if selected_account != st.session_state.selected_account:
        st.session_state.selected_account = selected_account
    
    st.divider()
    st.write(f"Current Account: **{st.session_state.selected_account}**")

# Main page content
st.header("Dashboard")
st.write(f"Welcome to the League of Analytics dashboard!")
st.write(f"You have selected: **{st.session_state.selected_account}**")
