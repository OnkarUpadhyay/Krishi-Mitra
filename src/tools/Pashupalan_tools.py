import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults


# ==========================================
# 1. SUDHA DAIRY PROCUREMENT CALCULATOR
# ==========================================

class SudhaRateInput(BaseModel):
    fat_percentage: float = Field(description="The fat percentage in the milk (e.g., 3.5).")
    snf_percentage: float = Field(description="The Solid-Not-Fat percentage in the milk (e.g., 8.5).")
    milk_type: str = Field(description="Type of milk: 'cow' or 'buffalo'.")


@tool("sudha_dairy_rate_card", args_schema=SudhaRateInput)
def sudha_dairy_rate_card(fat_percentage: float, snf_percentage: float, milk_type: str) -> str:
    """
    Calculates the estimated procurement price of milk based on the Bihar State Milk Co-operative Federation (Sudha) rate chart.
    Use this to help farmers understand the value of their milk before they sell it to the local dairy cooperative.
    """
    # Base rates change seasonally, these are current representative standards for Sudha Dairy
    base_rate = 32.0 if milk_type.lower() == "cow" else 42.0
    
    # Simple logic: Price increases linearly with fat and SNF quality
    fat_bonus = (fat_percentage - 3.5) * 5.0
    snf_bonus = (snf_percentage - 8.5) * 2.0
    
    final_rate = max(base_rate + fat_bonus + snf_bonus, 20.0)
    
    return json.dumps({
        "milk_type": milk_type.title(),
        "fat_content": f"{fat_percentage}%",
        "snf_content": f"{snf_percentage}%",
        "estimated_procurement_rate_inr_per_liter": round(final_rate, 2),
        "note": "Final payment is determined by the local milk collection center's electronic fat-testing machine."
    })


# ==========================================
# 2. CATTLE FEED OPTIMIZER (Nutritional Balance)
# ==========================================


class FeedOptimizerInput(BaseModel):
    cattle_type: str = Field(description="Type: 'milch' (lactating) or 'dry' (non-lactating).")
    daily_milk_yield: float = Field(description="Daily milk yield in liters (0 if dry).")
    body_weight_kg: float = Field(description="Estimated body weight in kg.")


@tool("cattle_feed_optimizer", args_schema=FeedOptimizerInput)
def cattle_feed_optimizer(cattle_type: str, daily_milk_yield: float, body_weight_kg: float) -> str:
    """
    Provides a balanced daily feeding schedule (Green fodder, Dry fodder, and Concentrates) 
    to maximize milk yield and cattle health.
    """
    # Baseline for a standard 400kg cow
    # Maintenance: 15-20kg green fodder + 5kg dry fodder + 1.5kg concentrate
    green_fodder = (body_weight_kg / 400) * 20
    dry_fodder = (body_weight_kg / 400) * 5
    
    # Production requirement: 1kg concentrate for every 2.5L of milk
    production_concentrate = daily_milk_yield / 2.5
    maintenance_concentrate = 1.5
    
    total_concentrate = maintenance_concentrate + production_concentrate if cattle_type == "milch" else 1.0
    
    return json.dumps({
        "feeding_plan": {
            "green_fodder_kg": round(green_fodder, 1),
            "dry_fodder_kg": round(dry_fodder, 1),
            "concentrate_mix_kg": round(total_concentrate, 2)
        },
        "advisory": "Ensure access to clean drinking water (60-80 liters/day) and mineral mixture (30-50g/day) for optimal yield."
    })


# ==========================================
# 3. VET CLINIC LOCATOR
# ==========================================

class VetLocatorInput(BaseModel):
    district: str = Field(description="The district in Bihar (e.g., Motihari, Patna).")
    block: str = Field(description="The block or Anchal in Bihar.")

@tool("vet_clinic_locator", args_schema=VetLocatorInput)
def vet_clinic_locator(district: str, block: str) -> str:
    """
    Locates the nearest Government Veterinary Hospital, Artificial Insemination (AI) center, 
    or veterinary services in a specific district and block in Bihar using real-time search.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY not found in environment variables."

    # Initialize Tavily search
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    
    # Focused search query targeting official Bihar government department listings
    query = f"Government veterinary hospital Artificial Insemination center address {block} {district} Bihar contact details"
    
    try:
        results = search.invoke({"query": query})
        
        if not results:
            return json.dumps({
                "status": "warning", 
                "message": f"Could not find specific veterinary centers for {block}, {district}."
            })
            
        formatted_reports = []
        for index, item in enumerate(results):
            url = item.get('url', 'Unknown')
            content = item.get('content', 'No content')
            formatted_reports.append(f"Source {index + 1} ({url}):\n{content}")
            
        return f"Veterinary Service Locations for {block}, {district}:\n\n" + "\n\n".join(formatted_reports)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Search failed: {str(e)}"})
    
pashupalan_tools_list = [sudha_dairy_rate_card, cattle_feed_optimizer, vet_clinic_locator]