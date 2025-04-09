from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from dotenv import load_dotenv
import asyncio

load_dotenv()

router = APIRouter(prefix="/firecrawl", tags=["firecrawl"])


@router.websocket("/ws/crawl")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        firecrawl_app = websocket.app.state.firecrawl_service
        logger.info("WebSocket connection established")
    except Exception as e:
        logger.error(f"Error initializing Firecrawl app: {e}")
        await websocket.close()
        return

    # Add ping/pong keepalive handler
    ping_task = None

    async def send_periodic_pings():
        try:
            while True:
                await asyncio.sleep(120)  # Send ping every 15 seconds
                await websocket.send_bytes(b"")  # Simple ping as empty bytes
                logger.debug("Ping sent to client")
        except asyncio.CancelledError:
            logger.debug("Ping task cancelled")
        except Exception as e:
            logger.error(f"Error in ping task: {e}")

    try:
        # Start ping keepalive task
        ping_task = asyncio.create_task(send_periodic_pings())

        data = await websocket.receive_json()
        url = data.get("url")
        limit = data.get("limit", 500)

        # Define WebSocket event handlers that don't block
        async def on_document(detail):
            try:
                await websocket.send_json(
                    {
                        "event": "document",
                        "url": detail["data"]["metadata"].get("url", "unknown"),
                    }
                )
                # Process document in a separate task to avoid blocking
                asyncio.create_task(process_document_async(detail))
            except Exception as e:
                logger.error(f"Error in document handler: {e}")

        async def process_document_async(detail):
            # Process document asynchronously to avoid blocking
            try:
                firecrawl_app.on_document(detail)
            except Exception as e:
                logger.error(f"Error processing document: {e}")

        async def on_error(detail):
            try:
                await websocket.send_json(
                    {"event": "error", "error": detail.get("error", "unknown error")}
                )
                firecrawl_app.on_error(detail)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

        async def on_done(detail):
            try:
                await websocket.send_json(
                    {"event": "done", "status": detail.get("status", "done")}
                )
                firecrawl_app.on_done(detail)
            except Exception as e:
                logger.error(f"Error in done handler: {e}")

        # Set root_url before crawling
        firecrawl_app.root_url = url.rstrip("/")

        # Send initial success message
        await websocket.send_json(
            {"event": "success", "message": f"Starting crawl of {url}"}
        )

        # Get the watcher and set up event listeners with async handlers
        watcher = firecrawl_app.app.crawl_url_and_watch(url, {"limit": limit})
        watcher.add_event_listener(
            "document", lambda detail: asyncio.create_task(on_document(detail))
        )
        watcher.add_event_listener(
            "error", lambda detail: asyncio.create_task(on_error(detail))
        )
        watcher.add_event_listener(
            "done", lambda detail: asyncio.create_task(on_done(detail))
        )

        # Start the watcher
        await watcher.connect()

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

    except Exception as e:
        logger.error(f"Error during WebSocket connection: {e}")
        await websocket.send_json({"event": "error", "error": str(e)})

    finally:
        # Ensure proper cleanup
        if ping_task:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
        await websocket.close()
