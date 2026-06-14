import requests
import json
import os
from langchain.tools import tool
from pydantic import BaseModel, Field

class MarketPriceInput(BaseModel):
    crop_name: str = Field(description="Name of the crop (e.g., Makhana, Maize, Litchi, Wheat).")
    mandi_location: str = Field(description="The local market or district (e.g., Gulabbagh, Samastipur).")

@tool("agmarknet_price_scraper", args_schema=MarketPriceInput)
def agmarknet_price_scraper(crop_name: str, mandi_location: str) -> str:
    """
    Fetches real-time wholesale market prices using the official Open Government Data (OGD) API for Agmarknet.
    """
    # Fetch the API key from your environment variables
    api_key = os.getenv("OGD_API_KEY") 
    if not api_key:
        return "System Error: OGD_API_KEY not found in environment variables. Admin must register at data.gov.in."
    
    # The specific Resource ID for Daily Wholesale Prices of Agricultural Commodities
    resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
    url = f"https://api.data.gov.in/resource/{resource_id}"
    
    # Build query parameters to filter specifically for Bihar, the district, and the crop
    params = {
        "api-key": api_key,
        "format": "json",
        "filters[state]": "Bihar",
        "filters[district]": mandi_location.title(),
        "filters[commodity]": crop_name.title(),
        "limit": 3 # We only need the most recent entries
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        records = data.get("records", [])
        
        if not records:
            return json.dumps({
                "status": "error", 
                "message": f"No recent Agmarknet data found for {crop_name} in {mandi_location}."
            })
        
        # Extract the most relevant data points from the latest record
        latest = records[0]
        return json.dumps({
            "market": latest.get("market"),
            "commodity": latest.get("commodity"),
            "arrival_date": latest.get("arrival_date"),
            "min_price_inr": latest.get("min_price"),
            "max_price_inr": latest.get("max_price"),
            "modal_price_inr": latest.get("modal_price"),
            "unit": "Quintal" # Agmarknet standardizes wholesale pricing in Quintals
        })
        
    except requests.exceptions.RequestException as e:
        return json.dumps({"status": "error", "message": f"OGD API fetch failed: {str(e)}"})

mandi_tools_list = [agmarknet_price_scraper]