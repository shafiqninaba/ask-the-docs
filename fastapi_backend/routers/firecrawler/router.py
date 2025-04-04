from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi_backend.models.firecrawl import CrawlRequest
from loguru import logger
from uuid import uuid4
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/firecrawl",
    tags=["firecrawl"]
)

async def crawl_generator(firecrawl_service, url, limit):
    """Generator for SSE events"""
    queue = asyncio.Queue()
    
    def on_document(detail):
        logger.info(f"Document event received: {detail['data']['metadata']['url']}")
        queue.put_nowait({"event": "document", "data": detail})
        
    def on_error(detail):
        logger.error(f"Error event received: {detail}")
        queue.put_nowait({"event": "error", "data": detail})
        
    def on_done(detail):
        logger.info(f"Done event received: {detail}")
        queue.put_nowait({"event": "done", "data": detail})
    
    try:
        logger.info(f"Starting crawl for URL: {url} with limit: {limit}")
        watcher = firecrawl_service.app.crawl_url_and_watch(str(url), {"limit": limit})
        watcher.add_event_listener("document", on_document)
        watcher.add_event_listener("error", on_error)
        watcher.add_event_listener("done", on_done)
        
        await watcher.connect()
        logger.info("Connected to watcher successfully.")
        
        while True:
            event = await queue.get()
            logger.debug(f"Event dequeued: {event}")
            yield f"data: {json.dumps(event)}\n\n"
            
            if event["event"] == "done":
                logger.info("Crawl completed.")
                break
                
    except Exception as e:
        logger.exception(f"Exception occurred during crawl: {e}")
        yield f"data: {json.dumps({'event': 'error', 'data': {'error': str(e)}})}\n\n"

@router.get("/stream-crawl")
async def stream_crawl(url: str, request: Request, limit: int = 10):
    try:
        logger.info(f"Received stream-crawl request for URL: {url} with limit: {limit}")
        firecrawl_service = request.app.state.firecrawl_service
        return StreamingResponse(
            crawl_generator(firecrawl_service, url, limit),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))