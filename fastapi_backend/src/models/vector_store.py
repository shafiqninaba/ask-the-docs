"""
Vector Store Pydantic Models
"""

from pydantic import BaseModel


class DocumentInput(BaseModel):
    """Input model for adding a document to the vector store.

    Attributes:
        collection_name (str): Name of the collection to add the document to.
        document (str): The document content.
        metadata (dict): Metadata associated with the document.
        id (str): Unique identifier for the document.
    """

    collection_name: str
    document: str
    metadata: dict
    id: str


class SearchQuery(BaseModel):
    """
    Input model for searching in the vector store.

    Attributes:
        collection_name (str): Name of the collection to search in.
        query (str): The search query string.
    """

    collection_name: str
    query: str
