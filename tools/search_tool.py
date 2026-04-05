import os
from typing import Optional

try:
    from langchain_tavily import TavilySearch
except Exception:  # pragma: no cover
    TavilySearch = None


def get_search_tool():
    """Return a TavilySearch tool instance (lazy-initialized).

    This avoids failing imports when TAVILY_API_KEY isn't configured.
    """

    if TavilySearch is None:
        raise RuntimeError("langchain_tavily is not available")

    max_results = int(os.getenv("TAVILY_MAX_RESULTS", "4"))
    return_metadata = os.getenv("TAVILY_RETURN_METADATA", "true").lower() == "true"

    _search_tool = TavilySearch(max_results=max_results, return_metadata=return_metadata)
    return _search_tool

