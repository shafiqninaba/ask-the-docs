"""
Pydantic Models for the firecrawl API.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional


class CrawlRequest(BaseModel):
    """
    Request model for initiating a crawl.
    """

    url: HttpUrl
    limit: Optional[int] = 10
