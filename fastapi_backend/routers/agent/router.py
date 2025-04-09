from fastapi import APIRouter, Request
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat/{thread_id}")
async def agent_chat(thread_id: str, request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        collection_name = data.get("collection_name", "")

        # Run the agent with the configuration
        config = {"collection_name": collection_name, "thread_id": thread_id}

        # Create system message with collection context
        system_message = SystemMessage(
            content=f"You are an assistant helping with documentation. Use the '{collection_name}' collection to query relevant information from the vector store ONLY IF you deem that it is required. If you query from the vector store, please provide the source of the information that can be found in the metadata."
        )

        # Add system message to config
        config["system_message"] = system_message

        # Convert the user message to a proper HumanMessage object
        user_message = HumanMessage(content=message)

        # Initialize messages for this run
        messages = [system_message, user_message]

        # Invoke the graph without streaming
        result = request.app.state.graph.invoke({"messages": messages}, config=config)

        # Extract the assistant's response from the result
        assistant_message = result["messages"][-1]
        response_content = ""

        if assistant_message.type == "ai" and hasattr(assistant_message, "content"):
            response_content = assistant_message.content

        return {"response": response_content, "thread_id": thread_id}

    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        return JSONResponse(
            status_code=500, content={"error": f"Error processing request: {str(e)}"}
        )
