import os
from langchain_tavily import TavilySearch

# Load Tavily configuration from environment variables
max_results = int(os.getenv("TAVILY_MAX_RESULTS", "4"))
return_metadata = os.getenv("TAVILY_RETURN_METADATA", "true").lower() == "true"

search_tool = TavilySearch(max_results=max_results, return_metadata=return_metadata)
