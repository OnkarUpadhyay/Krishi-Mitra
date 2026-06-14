import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# ==========================================
# 1. COLD STORAGE & WAREHOUSE LOCATOR
# ==========================================
class StorageLocatorInput(BaseModel):
    district: str = Field(description="The district in Bihar (e.g., Patna, Motihari, Muzaffarpur).")
    commodity: str = Field(description="The produce to store (e.g., potato, litchi, seeds).")

@tool("cold_storage_locator_api", args_schema=StorageLocatorInput)
def cold_storage_locator_api(district: str, commodity: str) -> str:
    """
    Locates cold storage and warehouse facilities in Bihar using real-time search.
    Use this to help farmers prevent distress sales by finding safe storage options.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    
    # Target Bihar State Warehousing Corporation (BSWC) and private cold chain operators
    query = f"cold storage warehouse facilities for {commodity} in {district} Bihar BSWC private cold chain"
    
    try:
        results = search.invoke({"query": query})
        if not results:
            return json.dumps({"status": "warning", "message": f"No cold storage facilities found for {commodity} in {district}."})
            
        reports = [f"Source: {item.get('url')}\n{item.get('content')}" for item in results]
        return "Found storage options:\n\n" + "\n\n".join(reports)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==========================================
# 2. CUSTOM HIRING CENTER (CHC) LOCATOR
# ==========================================
class CHCInput(BaseModel):
    district: str = Field(description="The district in Bihar.")
    machinery_type: str = Field(description="e.g., tractor, thresher, seed drill, reaper.")

@tool("custom_hiring_center_locator", args_schema=CHCInput)
def custom_hiring_center_locator(district: str, machinery_type: str) -> str:
    """
    Locates government-subsidized Custom Hiring Centers (CHCs) for renting agricultural machinery.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    
    # Official Bihar Mechanization Portal (farmech.bihar.gov.in)
    query = f"Custom Hiring Center {machinery_type} rental {district} Bihar farmech.bihar.gov.in"
    
    try:
        results = search.invoke({"query": query})
        reports = [f"Source: {item.get('url')}\n{item.get('content')}" for item in results] if results else ["No centers found."]
        return "Found Custom Hiring options:\n\n" + "\n\n".join(reports)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

supplychain_tools_list = [cold_storage_locator_api, custom_hiring_center_locator]