"""
This script defines the state of the agent workflow.
This module contains the state of the agent, which is a dictionary with messages and collection name.
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of the agent workflow. It contains the messages and collection name.
    The messages are a sequence of BaseMessage objects, and the collection name is a string.
    """

    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]
    collection_name: str
