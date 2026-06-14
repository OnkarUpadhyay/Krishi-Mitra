import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the DuckDuckGo Search wrapper
ddg_search = DuckDuckGoSearchRun()

class SeedAvailabilityInput(BaseModel):
    crop_name: str = Field(description="The name of the crop (e.g., Wheat, Paddy, Lentil).")
    district: str = Field(description="The district in Bihar (e.g., East Champaran, Patna).")

@tool("brbn_seed_availability_search", args_schema=SeedAvailabilityInput)
def brbn_seed_availability_search(crop_name: str, district: str) -> str:
    """
    Searches the live web for the current subsidized seed varieties, availability, 
    and pricing under the Bihar Rajya Beej Nigam (BRBN) or DBT Agriculture for a specific crop and district.
    """
    # Strict prompt targeting Bihar, the specific crop, and government subsidies
    query = f"Bihar BRBN subsidized {crop_name} seed varieties availability {district} latest official news"
    
    try:
        # Execute the live search
        results = ddg_search.invoke({"query": query})
        
        if not results:
             return json.dumps({
                 "status": "error", 
                 "message": f"Could not retrieve recent data for {crop_name} seeds in {district}. Advise the farmer to check the DBT Agriculture portal or contact their local Kisan Salahkar."
             })
             
        # Return structured context for the LLM to read and synthesize
        return json.dumps({
            "source": "DuckDuckGo Live Web Search (BRBN Fallback)",
            "location": district.title(),
            "crop": crop_name.title(),
            "live_search_data": results,
            "system_instruction": (
                "Read the 'live_search_data'. Identify any specific high-yielding or biofortified seed varieties "
                "(e.g., Rajendra-Gehun-3, Sabour Aayush) and the exact subsidy percentage (typically 50% to 90%). "
                "If district-specific data is missing, provide the general Bihar state subsidy guidelines for this crop. "
                "Do not hallucinate seed names; only use what is explicitly found in the live_search_data."
            )
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Search tool failed: {str(e)}"})

# ==========================================
# EXPORT LIST
# ==========================================
beej_tools_list = [brbn_seed_availability_search]