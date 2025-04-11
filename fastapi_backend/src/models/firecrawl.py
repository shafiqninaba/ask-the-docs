from pydantic import BaseModel, HttpUrl
from typing import Optional


class CrawlRequest(BaseModel):
    url: HttpUrl
    limit: Optional[int] = 10
