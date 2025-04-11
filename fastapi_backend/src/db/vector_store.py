from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from loguru import logger


class VectorStore:
    def __init__(self, client: QdrantClient):
        """Initialize the VectorStore with a Qdrant client.

        Args:
            client (QdrantClient): The Qdrant client instance.
        """
        self.client = client

    def add_documents(
        self, collection_name: str, document: str, metadata: dict, id: str
    ):
        """Add documents to the vector store.

        Args:
            collection_name (str): The name of the collection to add the document to.
            document (str): The document content.
            metadata (dict): Metadata associated with the document.
            id (str): The ID for the document.
        """
        logger.info(f"Adding document to {collection_name} with ID {id}")
        return self.client.add(
            collection_name=collection_name,
            documents=[document],
            metadata=[metadata],
            ids=[id],
        )

    async def search_result(self, collection_name: str, query: str):
        """Search for a result in the vector store.

        Args:
            collection_name (str): The name of the collection to search in.
            query (str): The search query.

        Returns:
            The search results from the vector store.
        """
        return self.client.query(
            collection_name=collection_name, query_text=query, limit=1
        )

    def create_collection(self, collection_name: str):
        """Create a new collection in the vector store.

        Args:
            collection_name (str): The name of the collection to create.
        """
        logger.info(f"Creating collection: {collection_name}")
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")

    def get_collections(self):
        """Get all collections in the vector store.

        Args:
            None

        Returns:
            List of all collections in the vector store.
        """
        logger.info("Fetching all collections")
        return self.client.get_collections()
