import streamlit as st

# GitHub link
GITHUB_URL = "https://github.com/shafiqninaba/ask-the-docs"
LINKEDIN_URL = "https://www.linkedin.com/in/shafiq-ninaba"


# Footer function
def display_footer():
    """Display the footer with GitHub and LinkedIn links."""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center;">
            <a href="{}" target="_blank">
                <img src="https://img.icons8.com/fluent/48/000000/github.png" alt="GitHub" width="30"/>
            </a>
            <a href="{}" target="_blank">
                <img src="https://img.icons8.com/fluent/48/000000/linkedin.png" alt="LinkedIn" width="30"/>
            </a>
        </div>
        """.format(GITHUB_URL, LINKEDIN_URL),
        unsafe_allow_html=True,
    )
