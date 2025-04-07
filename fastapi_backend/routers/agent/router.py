from fastapi import APIRouter
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi_backend.askthedocs_agent.agent import graph
from uuid import uuid4
import asyncio
import json

load_dotenv()

router = APIRouter(prefix="/chat", tags=["firecrawl"])


class QueryInput(BaseModel):
    user_query: str
    collection_name: str
    thread_id: str = None


@router.post("/chat/stream")
async def stream_chat(query_input: QueryInput):
    async def event_generator():
        try:
            thread_id = query_input.thread_id if query_input.thread_id else str(uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            # Add collection context to the user query
            enhanced_query = f"Using the '{query_input.collection_name}' collection, {query_input.user_query}"

            # Stream responses from LangGraph
            events = graph.stream(
                {"messages": [{"role": "user", "content": enhanced_query}]},
                config,
                stream_mode="values",
            )

            # Send thread_id as first message
            yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': thread_id})}\n\n"

            # Stream each token/chunk as it becomes available
            for event in events:
                if "messages" in event and len(event["messages"]) > 0:
                    message = event["messages"][-1].content
                    yield f"data: {json.dumps({'type': 'content', 'content': message})}\n\n"

                    # Small delay to avoid overwhelming the client
                    await asyncio.sleep(0.01)

            # Signal completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
