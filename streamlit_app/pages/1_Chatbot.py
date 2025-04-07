import streamlit as st
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import os
import uuid
import asyncio
import websockets
import json
from streamlit.runtime.scriptrunner import add_script_run_ctx
import threading

load_dotenv()

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")
# Convert HTTP URL to WebSocket URL
WS_BACKEND = FASTAPI_BACKEND.replace("http://", "ws://").replace("https://", "wss://")


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


async def communicate_via_websocket(prompt, message_placeholder):
    accumulated_response = ""
    websocket_url = f"{WS_BACKEND}/agent/ws/{st.session_state.thread_id}"

    async with websockets.connect(websocket_url) as ws:
        # Send the message with collection_name as JSON
        await ws.send(
            json.dumps(
                {
                    "message": prompt,
                    "collection_name": st.session_state.selected_collection,
                }
            )
        )

        # Receive streaming responses
        while True:
            try:
                message = await ws.recv()

                # Check if message is valid JSON and potentially contains control information
                try:
                    data = json.loads(message)
                    # Only display final output or delta tokens, not intermediate steps
                    if "type" in data:
                        if data["type"] == "final":
                            accumulated_response = data.get("content", "")
                            message_placeholder.markdown(accumulated_response)
                        elif data["type"] == "delta":
                            # For token-by-token streaming
                            accumulated_response += data.get("content", "")
                            message_placeholder.markdown(accumulated_response)
                    else:
                        # Regular message content
                        accumulated_response = data.get("content", message)
                        message_placeholder.markdown(accumulated_response)
                except json.JSONDecodeError:
                    # Plain text message, just append it
                    accumulated_response += message
                    message_placeholder.markdown(accumulated_response)

            except websockets.exceptions.ConnectionClosed:
                break

    # Only add the final accumulated response to the chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": accumulated_response}
    )


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

        # Run the WebSocket communication
        loop = asyncio.new_event_loop()

        def run_async_in_thread(loop, coro):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro)

        thread = threading.Thread(
            target=run_async_in_thread,
            args=(loop, communicate_via_websocket(prompt, message_placeholder)),
        )
        add_script_run_ctx(thread)
        thread.start()
        thread.join()
