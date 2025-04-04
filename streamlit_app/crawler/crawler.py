import streamlit as st
import requests
import json
from sseclient import SSEClient
from urllib.parse import urljoin
from dotenv import load_dotenv
import os

load_dotenv()

st.title("Website Crawler")

url = st.text_input("Enter website URL to crawl:", "https://example.com")
limit = st.number_input("Maximum pages to crawl:", min_value=1, value=10)

if st.button("Start Crawling"):
    crawl_url = urljoin(os.getenv("FASTAPI_BACKEND"), f"/firecrawl/stream-crawl?url={url}&limit={limit}")
    
    # Create a container for the progress
    progress_container = st.empty()
    progress_container.text("Starting crawl...")
    
    # Create a container for the results
    results = []
    results_container = st.container()
    
    try:
        messages = SSEClient(crawl_url)
        for msg in messages:
            data = json.loads(msg.data)
            event_type = data["event"]
            
            if event_type == "document":
                url = data["data"]["data"]["metadata"]["url"]
                results.append(url)
                # Update the display with all URLs found so far
                with results_container:
                    st.write(f"Found {len(results)} pages:")
                    for url in results:
                        st.write(f"- {url}")
            
            elif event_type == "error":
                progress_container.error(f"Error: {data['data']['error']}")
                break
            
            elif event_type == "done":
                progress_container.success("Crawl completed!")
                break
                
    except Exception as e:
        progress_container.error(f"Connection error: {str(e)}")