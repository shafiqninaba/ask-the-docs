from fastapi import APIRouter, WebSocket
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

router = APIRouter(prefix="/agent", tags=["agent"])


@router.websocket("/ws/{thread_id}")
async def agent_websocket(websocket: WebSocket, thread_id: str):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        message = data.get("message", "")
        collection_name = data.get("collection_name", "")

        # Send acknowledgment
        await websocket.send_json(
            {"type": "info", "content": "Processing your request..."}
        )

        # Run the agent and send only final outputs
        config = {"collection_name": collection_name, "thread_id": thread_id}

        # Create system message with collection context
        system_message = SystemMessage(
            content=f"You are an assistant helping with documentation. Use the '{collection_name}' collection to query relevant information from the vector store ONLY IF you deem that it is required. If you query from the vector store, please provide the source of the information that can be found in the metadata."
        )

        # Add system message to config
        config["system_message"] = system_message

        # Convert the user message to a proper HumanMessage object

        user_message = HumanMessage(content=message)

        # Keep track of the final response
        final_response = ""

        # Initialize messages for this run
        messages = [system_message, user_message]

        # Start the stream with proper initial messages instead of just the user message
        for event in websocket.app.state.graph.stream(
            {"messages": messages}, config=config, stream_mode="values"
        ):
            if "messages" in event and len(event["messages"]) > 0:
                # Get the newest message
                newest_message = event["messages"][-1]

                if newest_message.type == "ai" and hasattr(newest_message, "content"):
                    # For token-by-token streaming
                    token = newest_message.content
                    if isinstance(token, str):
                        final_response = token  # Replace with latest complete response
                        await websocket.send_json({"type": "delta", "content": token})
            elif event.get("type") == "on_chat_model_stream":
                # This is a token-by-token update
                token = event.get("data", "")
                final_response += token  # Accumulate the response
                await websocket.send_json({"type": "delta", "content": token})

        # Always send the final accumulated response without relying on memory
        await websocket.send_json({"type": "final", "content": final_response})

    except Exception as e:
        logger.error(f"Error in agent websocket: {e}")
        await websocket.send_json(
            {"type": "error", "content": f"Error processing request: {str(e)}"}
        )

    await websocket.close()
