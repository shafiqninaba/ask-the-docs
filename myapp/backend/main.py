from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from firecrawl import FirecrawlApp  # Adjust this import to your actual SDK/module
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

app = FastAPI()

# Allow Streamlit frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firecrawl_app = FirecrawlApp(api_url=os.environ.get("FIRECRAWL_API_URL"))  # Replace with your key

@app.websocket("/ws/crawl")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        url = data.get("url")
        limit = data.get("limit", 500)

        def on_document(detail):
            asyncio.create_task(websocket.send_json({
                "event": "document",
                "url": detail['data']['metadata'].get("url", "unknown")
            }))

        def on_error(detail):
            asyncio.create_task(websocket.send_json({
                "event": "error",
                "error": detail.get("error", "unknown error")
            }))

        def on_done(detail):
            asyncio.create_task(websocket.send_json({
                "event": "done",
                "status": detail.get("status", "done")
            }))

        watcher = firecrawl_app.crawl_url_and_watch(url, {'limit': limit})

        watcher.add_event_listener("document", on_document)
        watcher.add_event_listener("error", on_error)
        watcher.add_event_listener("done", on_done)

        await watcher.connect()

    except WebSocketDisconnect:
        logger.error("WebSocket disconnected")

    except Exception as e:
        await websocket.send_json({"event": "error", "error": str(e)})
