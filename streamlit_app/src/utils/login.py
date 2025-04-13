import streamlit as st
import hashlib


def authenticate():
    # Define the password
    CORRECT_PASSWORD = "14128ce9d7573671f28e95987d19bd40"

    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Authentication section
    if not st.session_state.authenticated:
        st.title("Ask the Docs - Login Required")

        # Simple password form
        with st.form("login_form"):
            password = st.text_input("Enter Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                if hashlib.md5(str.encode(password)).hexdigest() == CORRECT_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
