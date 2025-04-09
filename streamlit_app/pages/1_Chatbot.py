import streamlit as st
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import os
import uuid

load_dotenv()

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")


# Function to fetch collections from the API
def fetch_collections():
    try:
        response = requests.post(urljoin(FASTAPI_BACKEND, "/vector-store/collections"))
        data = response.json()
        collections = [collection["name"] for collection in data.get("collections", [])]
        return collections
    except Exception as e:
        st.error(f"Error fetching collections: {str(e)}")
        return []


# Show title and description
st.title("💬 Chatbot")

# Fetch collections and create dropdown
collections = fetch_collections()
if collections:
    # Initialize session state for selected collection if it doesn't exist
    if "selected_collection" not in st.session_state:
        st.session_state.selected_collection = collections[0]

    # Create the dropdown and update session state when changed
    selected_collection = st.selectbox(
        "Select Collection:",
        collections,
        index=collections.index(st.session_state.selected_collection)
        if st.session_state.selected_collection in collections
        else 0,
    )
    st.session_state.selected_collection = selected_collection
else:
    st.warning("No collections available. Please check your API connection.")

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


def get_chat_response(prompt):
    """Get chat response from FastAPI backend using POST request"""
    try:
        endpoint = urljoin(FASTAPI_BACKEND, f"/agent/chat/{st.session_state.thread_id}")
        payload = {
            "message": prompt,
            "collection_name": st.session_state.selected_collection,
        }

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "No response received")

    except requests.RequestException as e:
        return f"Error communicating with backend: {str(e)}"


# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history and display
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create a placeholder for the assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        # Get response from FastAPI backend
        response = get_chat_response(prompt)

        # Update placeholder with the response
        message_placeholder.markdown(response)

        # Add response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
