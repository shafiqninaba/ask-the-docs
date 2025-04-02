from firecrawl import FirecrawlApp
from loguru import logger
from uuid import uuid4
from typing import Optional

class FirecrawlService:
    def __init__(self, firecrawl_api_url: str, vector_store):
        """Initialize FirecrawlService with the Firecrawl API URL."""
        self.app = FirecrawlApp(firecrawl_api_url)
        self.vector_store = vector_store
        self.root_url = None

    async def on_document(self, detail):
        """Handle document events by uploading to vector store."""
        try:
            document = detail['data'].get('text', '')
            metadata = {
                **detail['data'].get('metadata', {}),
                "root_url": self.root_url,
                "scraped_at": detail['data'].get('timestamp')
            }
            
            await self.vector_store.add_documents(
                collection_name=self.root_url,
                document=document,
                metadata=metadata,
                id=str(uuid4())
            )
            logger.info(f"Document uploaded for URL: {metadata['url']}")
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")

    def on_error(self, detail):
        logger.error(detail["error"])

    def on_done(self, detail):
        logger.info(f"Crawl finished: {detail['status']}")

    async def crawl_url(self, url: str, limit: Optional[int] = 10):
        """Start crawling the given URL."""
        self.root_url = str(url)
        
        try:
            watcher = self.app.crawl_url_and_watch(str(url), {"limit": limit})
            
            watcher.add_event_listener("document",self.on_document)
            watcher.add_event_listener("error", self.on_error)
            watcher.add_event_listener("done", self.on_done)

            await watcher.connect()
            return {"status": "success", "message": f"Started crawling {url}"}
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise