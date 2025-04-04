import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Firecrawl App", layout="centered")

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")

# replace http or https with ws or wss
WEBSOCKET_URL = FASTAPI_BACKEND.replace("http", "ws").replace("https", "wss") + "/ws/crawl"

# Initialize crawling state if not exists
if "is_crawling" not in st.session_state:
    st.session_state["is_crawling"] = False

st.title("🔥🌐 Firecrawler")
url = st.text_input("Enter a URL to crawl", "https://firecrawl.dev")
limit = st.slider("Maximum pages to crawl", min_value=10, max_value=1000, value=500, step=10)

# Disable button while crawling is active
if st.button("Start Crawl", disabled=st.session_state["is_crawling"]) and url:
    st.session_state["messages"] = []
    st.session_state["stats"] = {"pages": 0, "errors": 0}
    st.session_state["crawled_urls"] = []  # Add list to store crawled URLs
    st.session_state["is_crawling"] = True

    # Create empty placeholders for dynamic content OUTSIDE the loop
    stats_placeholder = st.empty()
    urls_placeholder = st.empty()
    messages_placeholder = st.empty()
    
    async def crawl():
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                await websocket.send(json.dumps({"url": url, "limit": limit}))
                
                try:
                    with st.spinner("Crawling in progress", show_time=True):
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
                        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state["is_crawling"] = False  # Reset on error

    asyncio.run(crawl())