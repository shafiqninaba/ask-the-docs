import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import time
from urllib.parse import urljoin

load_dotenv()

st.set_page_config(page_title="Firecrawl App", layout="centered")

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")

# replace http or https with ws or wss
WEBSOCKET_URL = urljoin(FASTAPI_BACKEND.replace("http", "ws").replace("https", "wss"),"/ws/crawl")

# Initialize crawling state if not exists
if "is_crawling" not in st.session_state:
    st.session_state["is_crawling"] = False
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None

st.title("🔥🌐 Firecrawler")
url = st.text_input("Enter a URL to crawl", "https://firecrawl.dev")
limit = st.slider("Maximum pages to crawl", min_value=10, max_value=1000, value=500, step=10)

# Button container that will be conditionally shown/hidden
button_container = st.empty()

# Only show the button if we're not currently crawling
if not st.session_state["is_crawling"]:
    if button_container.button("Start Crawl", key="start_crawl_button") and url:
        st.session_state["messages"] = []
        st.session_state["stats"] = {"pages": 0, "errors": 0}
        st.session_state["crawled_urls"] = []  # Add list to store crawled URLs
        st.session_state["is_crawling"] = True
        st.session_state["start_time"] = time.time()
        
        # Clear the button once crawling starts
        button_container.empty()

# Create spinner container outside the crawler logic
spinner_container = st.empty()

# If crawling is active, show the time elapsed spinner
if st.session_state["is_crawling"]:
    # Create empty placeholders for dynamic content
    stats_placeholder = st.empty()
    urls_placeholder = st.empty()
    messages_placeholder = st.empty()
    
    async def crawl():
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                await websocket.send(json.dumps({"url": url, "limit": limit-1}))
                
                try:
                    with st.spinner("Crawling in progress...", show_time=True):
                      while True:                            
                            message = await websocket.recv()
                            data = json.loads(message)
                            timestamp = datetime.now().strftime("%H:%M:%S")

                            if data["event"] == "document":
                                st.session_state["stats"]["pages"] += 1
                                st.session_state["messages"].append({
                                    "type": "document",
                                    "content": f"Crawled: {data['url']}",
                                    "time": timestamp
                                })
                                st.session_state["crawled_urls"].append({
                                    "url": data['url'],
                                    "time": timestamp
                                })
                            elif data["event"] == "error":
                                st.session_state["stats"]["errors"] += 1
                                st.session_state["messages"].append({
                                    "type": "error",
                                    "content": f"Error: {data['error']}",
                                    "time": timestamp
                                })
                            elif data["event"] == "done":
                                st.session_state["messages"].append({
                                    "type": "done",
                                    "content": f"Done: {data['status']}",
                                    "time": timestamp
                                })
                                st.session_state["is_crawling"] = False
                                st.session_state["start_time"] = None
                                # Clear the spinner
                                spinner_container.empty()
                                break

                            # Update stats display
                            with stats_placeholder.container():
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Pages Crawled", st.session_state["stats"]["pages"])
                                with col2:
                                    st.metric("Errors", st.session_state["stats"]["errors"])
                            
                            # Update URLs display
                            with urls_placeholder.container(height=200):
                                urls_to_show = st.session_state["crawled_urls"]
                                for url_item in urls_to_show:
                                    st.text(f"{url_item['time']} - {url_item['url']}")
                                    
                except websockets.exceptions.ConnectionClosedOK:
                    # Connection closed normally, make sure we show the final status
                    if st.session_state["messages"] and "done" not in [m["type"] for m in st.session_state["messages"]]:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        st.session_state["messages"].append({
                            "type": "done",
                            "content": "Crawl completed",
                            "time": timestamp
                        })
                        st.success("Crawl completed!", icon="✅")
                        st.session_state["is_crawling"] = False  # Mark crawling as complete
                        st.session_state["start_time"] = None
                        button_container.button("Start Crawl", key="restart_crawl_button")  # Added unique key

                        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state["is_crawling"] = False  # Reset on error
            st.session_state["start_time"] = None

    asyncio.run(crawl())