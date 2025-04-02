from fastapi import APIRouter, Request, HTTPException
from fastapi_backend.models.firecrawl import CrawlRequest
from loguru import logger

router = APIRouter(
    prefix="/firecrawl",
    tags=["firecrawl"]
)

@router.post("/crawl")
async def start_crawl(
    crawl_request: CrawlRequest,
    request: Request
):
    try:
        firecrawl_service = request.app.state.firecrawl_service
        
        result = await firecrawl_service.crawl_url(
            url=crawl_request.url,
            limit=crawl_request.limit
        )
        
        return result
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))