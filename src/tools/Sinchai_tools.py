import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# ==========================================
# 1. SUBSIDY & SCHEME SEARCH (Mukhyamantri Nijee Nalkup Yojana)
# ==========================================
class SubsidySearchInput(BaseModel):
    query: str = Field(description="Search topic, e.g., 'Mukhyamantri Nijee Nalkup Yojana eligibility', 'borewell subsidy Bihar', 'irrigation pump set grant'.")

@tool("bihar_irrigation_subsidy_search", args_schema=SubsidySearchInput)
def bihar_irrigation_subsidy_search(query: str) -> str:
    """
    Searches for official government irrigation schemes, subsidy eligibility criteria (like borewells and pumps), 
    and application processes for farmers in Bihar using Tavily.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY missing."

    # Initializing Tavily search with a strict query to ensure localized Bihar data
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    search_query = f"Bihar Minor Water Resources Department {query} official guidelines subsidy eligibility application"
    
    try:
        results = search.invoke({"query": search_query})
        formatted_reports = [f"Source ({item.get('url')}):\n{item.get('content')}" for item in results]
        return "\n\n".join(formatted_reports)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==========================================
# 2. FIELD WATER REQUIREMENT CALCULATOR (Integrated with Tavily)
# ==========================================
class IrrigationCalcInput(BaseModel):
    crop_name: str = Field(description="Name of the crop.")
    soil_type: str = Field(description="Type of soil (e.g., clay, sandy, loam).")
    area_acre: float = Field(description="Land area in acres.")

@tool("irrigation_requirement_calculator", args_schema=IrrigationCalcInput)
def irrigation_requirement_calculator(crop_name: str, soil_type: str, area_acre: float) -> str:
    """
    Estimates the irrigation requirement based on crop type and soil water-holding capacity,
    leveraging Tavily to retrieve the latest Bihar-specific agricultural best practices.
    """
    # 1. First, get optimized local data via Tavily
    api_key = os.getenv("TAVILY_API_KEY")
    search = TavilySearchResults(max_results=1, tavily_api_key=api_key)
    search_query = f"recommended irrigation depth for {crop_name} in {soil_type} soil Bihar agricultural practices"
    
    local_advisory = "Standard FAO practices apply."
    try:
        results = search.invoke({"query": search_query})
        if results:
            local_advisory = results[0].get('content', local_advisory)
    except Exception as e:
        pass  # If search fails, we fall back to the standard advisory without crashing the tool.

    # 2. Perform the calculation
    # Baseline irrigation needs (cm/season for Bihar)
    needs = {"paddy": 120, "wheat": 45, "maize": 50, "sugarcane": 150}
    base_cm = needs.get(crop_name.lower(), 50)
    
    # Soil correction factor
    multiplier = {"sandy": 1.4, "loam": 1.0, "clay": 0.8}.get(soil_type.lower(), 1.0)
    total_volume_liters = (base_cm * area_acre * 4046.86 * multiplier) / 100
    
    return json.dumps({
        "crop": crop_name,
        "estimated_season_requirement_liters": round(total_volume_liters, 2),
        "local_advisory_context": local_advisory,
        "technical_note": f"For {soil_type} soil, prioritize drip or sprinkler systems to reduce evaporation loss."
    })

sinchai_tools_list = [bihar_irrigation_subsidy_search, irrigation_requirement_calculator]