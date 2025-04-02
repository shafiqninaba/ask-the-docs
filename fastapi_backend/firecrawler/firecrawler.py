from firecrawl import FirecrawlApp
from loguru import logger
from uuid import uuid4
from typing import Optional
import asyncio

class FirecrawlService:
    def __init__(self, firecrawl_api_url: str, vector_store):
        """Initialize FirecrawlService with the Firecrawl API URL."""
        self.app = FirecrawlApp(firecrawl_api_url)
        self.vector_store = vector_store
        self.root_url = None

    async def _process_document(self, detail):
        """Async handler for document processing."""
        try:
            document = detail['data'].get('markdown', '')
            metadata = {
                **detail['data'].get('metadata', {}),
                "root_url": self.root_url,
            }
            
            await self.vector_store.add_documents(
                collection_name=''.join([char for char in self.root_url if char.isalnum()]),
                document=document,
                metadata=metadata,
                id=str(uuid4())
            )
            logger.info(f"Document uploaded for URL: {metadata['url']}")
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")

    def on_document(self, detail):
        """Synchronous wrapper for document events that schedules async processing."""
        asyncio.create_task(self._process_document(detail))
        
    def on_error(self, detail):
        logger.error(detail["error"])

    def on_done(self, detail):
        logger.info(f"Crawl finished: {detail['status']}")

    async def crawl_url(self, url: str, limit: Optional[int] = 10):
        """Start crawling the given URL."""
        self.root_url = str(url).rstrip("/")
        try:
            watcher = self.app.crawl_url_and_watch(str(url), {"limit": limit})
            
            watcher.add_event_listener("document", self.on_document)
            watcher.add_event_listener("error", self.on_error)
            watcher.add_event_listener("done", self.on_done)

            await watcher.connect()
            return {"status": "success", "message": f"Started crawling {url}"}
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise