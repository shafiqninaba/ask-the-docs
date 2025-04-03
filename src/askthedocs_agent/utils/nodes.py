from langchain_openai import ChatOpenAI
from utils.state import State
from utils.tools import tools


llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}
