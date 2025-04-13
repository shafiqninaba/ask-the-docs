"""
Home page for the Streamlit app.
This page serves as the entry point for the application and provides an overview of its features.
"""

import streamlit as st
from streamlit_app.src.utils.footer import display_footer

st.set_page_config(page_title="Ask the Docs", page_icon="📚", layout="wide")

st.title("📚 Ask the Docs")
st.write("Welcome to Ask the Docs! Use the sidebar to navigate to different features.")

st.subheader("Features")
st.write(
    "- 🔥🌐 **Firecrawler**: Crawl websites to gather document content and upload to vector store"
)
st.write(
    "- 💬 **Chatbot**: Interact with your documents using a conversational interface"
)

st.subheader("How to Use")
st.write("1. **[Firecrawler](/Crawler)**: Enter a URL to crawl and gather documents. ")
st.write(
    "2. **[Chatbot](/Chatbot)**: Select a collection and start chatting with the documents."
)


display_footer()
