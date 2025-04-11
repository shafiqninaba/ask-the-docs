"""
Router for the agent endpoint.
It includes the chat endpoint that streams agent responses.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import pprint

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat/{thread_id}")
async def chat(thread_id: str, request: Request, payload: dict):
    """
    Endpoint to stream agent responses.

    Args:
        thread_id (str): The ID of the thread for the agent.
        request (Request): The FastAPI request object.
        payload (dict): The payload containing the message and collection name.

            {
                "message": "Your message here",
                "collection_name": "your_collection_name"
            }


    Returns:
        StreamingResponse: A streaming response that yields the agent's responses.
    """
    message = payload.get("message")
    collection_name = payload.get("collection_name")
    if not message or not collection_name:
        raise HTTPException(
            status_code=400, detail="Missing message or collection_name"
        )

    # Build the initial state for the agent graph with a system message included.
    state = {
        "messages": [
            {
                "role": "system",
                "content": f"You are an assistant helping with documentation. Use the '{collection_name}' collection to query relevant information from the vector store ONLY IF you deem that it is required. If you query from the vector store, please provide the source of the information that can be found in the metadata.",
            },
            {"role": "user", "content": message},
        ],
        "collection_name": collection_name,
    }

    graph = request.app.state.graph

    config = {"configurable": {"thread_id": thread_id}}

    def event_generator(config=config):
        # Iterate over the graph's streaming output
        for output in graph.stream(state, config=config):
            for key, value in output.items():
                # Log the output from each node
                pprint.pprint(f"Output from node '{key}':")
                pprint.pprint(value)
                # Yield the output as a server-sent event
                yield f"data: {value["messages"][0]}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
