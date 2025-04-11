"""
This page is the chatbot interface for the AskTheDocs application.
This page allows users to interact with the chatbot, select collections, and view conversation history.
"""

import streamlit as st
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import os
import uuid
import re


load_dotenv()

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")


# Function to fetch collections from the API
def fetch_collections():
    """
    Fetch collections from the FastAPI backend.
    This function makes a request to the FastAPI backend to retrieve the available collections.

    Returns:
        list: A list of collection names.
    """
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
        index=(
            collections.index(st.session_state.selected_collection)
            if st.session_state.selected_collection in collections
            else 0
        ),
    )
    # Clear conversation history when collection changes
    if st.session_state.selected_collection != selected_collection:
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.selected_collection = selected_collection
else:
    st.warning("No collections available. Please check your API connection.")

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


def extract_content(chunk):
    """
    Extract the content from the chunk using regex.

    Args:
        chunk (str): The chunk of text to extract content from.

    Returns:
        str: The extracted content.
    """
    # Using regex to extract the content between content=" or content=' and the closing quote
    pattern = r'content=(["\'])(.*?)\1 additional_kwargs='
    match = re.search(pattern, chunk, re.DOTALL)

    if match:
        # Get the captured content (group 2 contains the content)
        content = match.group(2)
        # Process escape sequences to convert \n to actual newlines
        content = content.encode().decode("unicode_escape")
        return content
    else:
        # If pattern not found, return empty string or error message
        return chunk


def get_chat_response(prompt, message_placeholder):
    """Get chat response from FastAPI backend using streaming response

    Args:
        prompt (str): The user input prompt.
        message_placeholder: Placeholder for the assistant response.

    Returns:
        str: The assistant's response.
    """
    try:
        endpoint = urljoin(FASTAPI_BACKEND, f"/agent/chat/{st.session_state.thread_id}")
        payload = {
            "message": prompt,
            "collection_name": st.session_state.selected_collection,
        }

        # Initialize an empty response that we'll build up
        full_response = ""
        current_stage = None

        # Display initial "thinking" message
        message_placeholder.markdown("Thinking...")

        # Use stream=True to get a streaming response
        with requests.post(endpoint, json=payload, stream=True) as response:
            response.raise_for_status()

            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    # Parse the SSE format "data: {value}"
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data:"):
                        # Extract the actual data content
                        chunk = line_text[5:].strip()

                        # Add the chunk to our full response
                        full_response += chunk

                        # Detect the current stage based on content
                        if (
                            "search_vector_store" in chunk
                            and current_stage != "searching"
                        ):
                            current_stage = "searching"
                            message_placeholder.markdown(
                                "🔍 Searching in "
                                + f"`{st.session_state.selected_collection}` "
                                + "for relevant information..."
                            )
                        elif (
                            "tavily_search_results" in chunk
                            and current_stage != "searching"
                        ):
                            current_stage = "searching"
                            message_placeholder.markdown(
                                "🌐 Searching the web for relevant information..."
                            )

                        elif (
                            "search_vector_store" in chunk
                            and current_stage == "searching"
                        ):
                            current_stage = "processing"
                            message_placeholder.markdown(
                                "📊 Processing search results..."
                            )

                        # Check if this is a final response (not a tool call or retrieved docs)
                        elif not any(
                            marker in chunk
                            for marker in [
                                "search_vector_store",
                                "tavily_search_results",
                                "gpt-4-0125-preview",
                            ]
                        ):
                            if current_stage != "answering":
                                current_stage = "answering"
                                answer = extract_content(chunk)
                                message_placeholder.markdown(
                                    answer, unsafe_allow_html=True
                                )
                                return answer

    except requests.RequestException as e:
        error_message = f"Error communicating with backend: {str(e)}"
        message_placeholder.markdown(error_message)
        return error_message


# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    # Add error handling for message structure
    role = message.get("role", "user")  # Default to "user" if role is missing
    content = message.get(
        "content", ""
    )  # Default to empty string if content is missing
    with st.chat_message(role):
        st.markdown(content, unsafe_allow_html=True)

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

        # Get response from FastAPI backend with streaming
        response = get_chat_response(prompt, message_placeholder)

        # Extract the final content from the full response
        final_content = extract_content(response)

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": final_content}
        )
