from pydantic import BaseModel

class DocumentInput(BaseModel):
    collection_name: str
    document: str
    metadata: dict
    id: str

class SearchQuery(BaseModel):
    collection_name: str
    query: str