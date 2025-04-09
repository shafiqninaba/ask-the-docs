from fastapi_backend.askthedocs_agent.utils.state import AgentState
from fastapi_backend.askthedocs_agent.utils.nodes import agent, rewrite, generate
from fastapi_backend.askthedocs_agent.utils.edges import grade_documents
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from fastapi_backend.askthedocs_agent.utils.tools import tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START

load_dotenv()


def create_graph():
    """
    Create a new graph for the agent. This function initializes the graph and adds
    nodes and edges to define the workflow of the agent.
    """
    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the nodes we will cycle between
    workflow.add_node("agent", agent)  # agent
    retrieve = ToolNode(tools)
    workflow.add_node("retrieve", retrieve)  # retrieval
    workflow.add_node("rewrite", rewrite)  # Re-writing the question
    workflow.add_node(
        "generate", generate
    )  # Generating a response after we know the documents are relevant
    # Call agent node to decide to retrieve or not
    workflow.add_edge(START, "agent")

    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "agent",
        # Assess agent decision
        tools_condition,
        {
            # Translate the condition outputs to nodes in our graph
            "tools": "retrieve",
            END: END,
        },
    )

    # Edges taken after the `action` node is called.
    workflow.add_conditional_edges(
        "retrieve",
        # Assess agent decision
        grade_documents,
    )
    workflow.add_edge("generate", END)
    workflow.add_edge("rewrite", "agent")

    graph = workflow.compile(checkpointer=MemorySaver())
    return graph
