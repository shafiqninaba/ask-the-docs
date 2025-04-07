from fastapi_backend.askthedocs_agent.utils.state import State
from fastapi_backend.askthedocs_agent.utils.nodes import chatbot
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from fastapi_backend.askthedocs_agent.utils.tools import tools
from langgraph.checkpoint.memory import MemorySaver
from uuid import uuid4

memory = MemorySaver()

load_dotenv()

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
graph = graph_builder.compile(checkpointer=memory)


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


if __name__ == "__main__":
    config = {"configurable": {"thread_id": str(uuid4())}}

    user_input = "Hi there! My name is Will."

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()

    user_input = "How do i implement a function in python?"

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()
