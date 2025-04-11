"""
This script defines the tools used in the agent workflow.
This module contains the function to search the vector store for relevant documents.
It also includes the TavilySearchResults tool for searching Tavily.
"""

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from dotenv import load_dotenv
import requests
import os
from urllib.parse import urljoin
from loguru import logger

load_dotenv()
tavily_tool = TavilySearchResults(max_results=2)

FASTAPI_BACKEND = os.getenv("FASTAPI_BACKEND")


@tool
def search_vector_store(collection_name: str, query: str):
    """Search the vector store for relevant documents.

    Args:
        collection_name: The name of the collection to search in
        query: The search query string

    Returns:
        The search results from the vector store. This includes their metadata which contains the sourceURL.
    """
    try:
        response = requests.post(
            urljoin(FASTAPI_BACKEND, "/vector-store/search"),
            json={"collection_name": collection_name, "query": query},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Add more detailed logging here
        logger.error(f"Error in search_vector_store: {str(e)}")
        return f"Error searching vector store: {str(e)}"


# Update the tools list to include your new tool
tools = [tavily_tool, search_vector_store]
