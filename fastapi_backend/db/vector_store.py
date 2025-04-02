from qdrant_client import QdrantClient
from loguru import logger

class VectorStore:
    def __init__(self, client: QdrantClient):
        self.client = client

    async def add_documents(self, collection_name: str, document: str, metadata: dict, id: str):
        """Add documents to the vector store."""
        return self.client.add(
            collection_name=collection_name,
            documents=[document],
            metadata=[metadata],
            ids=[id]
        )

    async def search_result(self, collection_name: str, query: str):
        """Search for a result in the vector store."""
        return self.client.query(
            collection_name=collection_name,
            query_text=query
        )