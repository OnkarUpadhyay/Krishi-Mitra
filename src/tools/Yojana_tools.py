import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

class YojanaSearchInput(BaseModel):
    scheme_name: str = Field(description="The scheme name to query (e.g., PM-Kisan, Diesel Subsidy, Krishi Yantra, Jal Jeevan Hariyali).")
    specific_query: str = Field(description="What the user wants to know (e.g., 'application deadline', 'eligibility criteria', 'subsidy amount', 'latest news').")

@tool("bihar_yojana_search_api", args_schema=YojanaSearchInput)
def bihar_yojana_search_api(scheme_name: str, specific_query: str) -> str:
    """
    Searches the web for current, official information regarding Bihar agriculture schemes (Yojanas).
    Use this to find eligibility rules, subsidy amounts, application deadlines, and official government updates.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY not found in environment variables."

    # Initialize Tavily. Limiting to 3 results keeps the context window tight and fast.
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    
    # We craft a highly strict prompt forcing the search to target official Bihar portals 
    # and recent news regarding the specific scheme.
    query = f"Bihar agriculture {scheme_name} {specific_query} official guidelines dbtagriculture.bihar.gov.in latest update"
    
    try:
        results = search.invoke({"query": query})
        
        if not results:
            return json.dumps({
                "status": "warning",
                "message": f"No current official updates or guidelines found for {scheme_name} regarding '{specific_query}'."
            })
            
        # Format the search results cleanly for the Groq model to read and synthesize
        formatted_reports = []
        for index, item in enumerate(results):
            url = item.get('url', 'Unknown')
            content = item.get('content', 'No content')
            formatted_reports.append(f"Source {index + 1} ({url}):\n{content}")
            
        return f"Recent Official Guidelines & News for {scheme_name} in Bihar:\n\n" + "\n\n".join(formatted_reports)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tavily Search failed: {str(e)}"})

yojana_tools_list = [bihar_yojana_search_api]