from fastapi import APIRouter, HTTPException
from fastapi_backend.models.vector_store import DocumentInput, SearchQuery
from fastapi_backend.db.vector_store import VectorStore
from fastapi import Request

router = APIRouter(prefix="/vector-store", tags=["vector-store"])


@router.post("/documents")
async def add_document(doc: DocumentInput, request: Request):
    try:
        vector_store: VectorStore = request.app.state.vector_store
        await vector_store.add_documents(
            collection_name=doc.collection_name,
            document=doc.document,
            metadata=doc.metadata,
            id=doc.id,
        )
        return {"message": f"Document {doc.id} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(query: SearchQuery, request: Request):
    try:
        vector_store: VectorStore = request.app.state.vector_store
        return await vector_store.search_result(
            collection_name=query.collection_name, query=query.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections")
def get_collections(request: Request):
    try:
        vector_store: VectorStore = request.app.state.vector_store
        return vector_store.get_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
