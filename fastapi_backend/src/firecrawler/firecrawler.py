"""
Firecrawl service for crawling and processing web pages.
"""

from firecrawl import FirecrawlApp
from loguru import logger
from uuid import uuid4
from typing import Optional


class FirecrawlService:
    def __init__(self, firecrawl_api_url: str, vector_store):
        """Initialize FirecrawlService with the Firecrawl API URL.

        Args:
            firecrawl_api_url (str): The URL for the Firecrawl API.
            vector_store: The vector store instance for storing crawled documents.
        """
        self.app = FirecrawlApp(firecrawl_api_url)
        self.vector_store = vector_store
        self.root_url = None

    def _process_document(self, detail):
        """Async handler for document processing.

        Args:
            detail: The detail of the document event.
        """
        try:
            document = detail["data"].get("markdown", "")
            metadata = {
                **detail["data"].get("metadata", {}),
                "root_url": self.root_url,
            }
            # drop document key from metadata if it exists
            metadata.pop("document", None)

            self.vector_store.add_documents(
                collection_name="".join(
                    [char for char in self.root_url if char.isalnum()]
                ),
                document=document,
                metadata=metadata,
                id=str(uuid4()),
            )
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")

    def on_document(self, detail):
        """Synchronous wrapper for document events that schedules async processing.

        Args:
            detail: The detail of the document event.
        """
        self._process_document(detail)

    def on_error(self, detail):
        """Handle error events.

        Args:
            detail: The detail of the error event.
        """
        logger.error(detail["error"])

    def on_done(self, detail):
        """Handle completion events.

        Args:
            detail: The detail of the completion event.
        """
        logger.info(f"Crawl finished: {detail['status']}")

    async def crawl_url(self, url: str, limit: Optional[int] = 10):
        """Start crawling the given URL.

        Args:
            url (str): The URL to crawl.
            limit (int, optional): The maximum number of pages to crawl. Defaults to 10.
        """
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
