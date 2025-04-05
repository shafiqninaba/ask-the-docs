import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import os

load_dotenv()

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")

# Function to fetch collections from the API
def fetch_collections():
    try:
        response = requests.post(urljoin(FASTAPI_BACKEND,"/vector-store/collections"))
        data = response.json()
        collections = [collection["name"] for collection in data.get("collections", [])]
        return collections
    except Exception as e:
        st.error(f"Error fetching collections: {str(e)}")
        return []


# Show title and description.
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

# Create an OpenAI client.
client = ChatOpenAI(model="gpt-4o-mini", streaming=True)

# Create a session state variable to store the chat messages.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a chat input field
if prompt := st.chat_input("What is up?"):
    # You can now access the selected collection with:
    # st.session_state.selected_collection

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Convert session messages to LangChain format
    langchain_messages = []
    for m in st.session_state.messages:
        if m["role"] == "user":
            langchain_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            langchain_messages.append(AIMessage(content=m["content"]))

    # Stream the response to the chat using LangChain
    with st.chat_message("assistant"):
        response = ""
        message_placeholder = st.empty()

        # Use LangChain's streaming capability
        for chunk in client.stream(langchain_messages):
            response += chunk.content
            message_placeholder.markdown(response + "▌")
        message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
