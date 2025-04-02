from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import os
from qdrant_client import QdrantClient
from fastapi_backend.db.vector_store import VectorStore
from fastapi_backend.firecrawler.firecrawler import FirecrawlService
from fastapi_backend.routers.vector_store.router import router as vector_store_router
from fastapi_backend.routers.firecrawler.router import router as firecrawl_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_dotenv()
    
    # Check required environment variables
    if not os.environ.get("QDRANT_URL"):
        raise ValueError("QDRANT_URL environment variable is not set")
    if not os.environ.get("FIRECRAWL_API_URL"):
        raise ValueError("FIRECRAWL_API_URL environment variable is not set")
    
    # Initialize Vector Store
    qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL"))
    app.state.vector_store = VectorStore(qdrant_client)
    logger.info("Vector store initialized")
    
    # Initialize Firecrawl Service
    app.state.firecrawl_service = FirecrawlService(
        firecrawl_api_url=os.environ.get("FIRECRAWL_API_URL"),
        vector_store=app.state.vector_store
    )
    
    logger.info("Firecrawl service initialized")
    
    yield
    
    # Cleanup
    await qdrant_client.close()
    logger.info("Vector store connection closed")

app = FastAPI(lifespan=lifespan)
app.include_router(vector_store_router)
app.include_router(firecrawl_router)