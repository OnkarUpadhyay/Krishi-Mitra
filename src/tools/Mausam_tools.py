import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
import requests
# Load environment variables from .env file (e.g., TAVILY_API_KEY)
load_dotenv()


# ==========================================
# 1. FLOOD ALERT TOOL (Using Tavily Search)
# ==========================================
class FloodAlertInput(BaseModel):
    river_basin: str = Field(description="The river basin to check (e.g., Kosi, Gandak, Bagmati, Ganga).")
    district: str = Field(description="The district in Bihar to check for flood risks.")

@tool("kosi_gandak_flood_alert_api", args_schema=FloodAlertInput)
def kosi_gandak_flood_alert_api(river_basin: str, district: str) -> str:
    """
    Searches the web for real-time flood alerts, barrage discharge data (cusecs), and river water levels in Bihar.
    Use this when users ask about flood risks, barrage status, or river danger levels.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY not found in environment variables."

    # Initialize Tavily. We limit to 3 results to keep the prompt context tight 
    # and focused on the most recent, relevant news/alerts.
    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    
    # We craft a highly strict, localized prompt for the search engine to force it 
    # to look for current operational data rather than historical wiki pages.
    query = f"current water level flood status {river_basin} river {district} Bihar barrage discharge news today"
    
    try:
        # Execute the search
        results = search.invoke({"query": query})
        
        if not results:
            return json.dumps({
                "status": "warning",
                "message": f"No recent flood alerts or news found for the {river_basin} river in {district} today."
            })
            
        # Format the search results into a clean string for the LLM to parse
        formatted_reports = []
        for index, item in enumerate(results):
            # item typically contains 'url' and 'content' (the summarized text)
            formatted_reports.append(f"Source {index + 1} ({item.get('url', 'Unknown')}):\n{item.get('content', 'No content')}")
            
        # We return the raw text reports. The Groq LLM running the Mausam Agent 
        # will naturally read this, synthesize the facts, and output a clean answer.
        return f"Recent Search Reports for {river_basin} in {district}:\n\n" + "\n\n".join(formatted_reports)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tavily Search failed: {str(e)}"})

# ==========================================
# 2. WEATHER TOOL (Placeholder)
# ==========================================
class WeatherInput(BaseModel):
    district: str = Field(description="The district in Bihar.")

@tool("imd_district_weather", args_schema=WeatherInput)
def imd_district_weather(district: str) -> str:
    """
    Fetches the 3-day micro-climate and weather forecast for a specific district.
    Use this when users ask about rain, temperatures, or general weather conditions.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "System Error: OPENWEATHER_API_KEY not found in environment variables."

    # OpenWeatherMap 5-day/3-hour forecast endpoint
    # Appending ',Bihar,IN' ensures the geocoder targets the correct Indian district
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": f"{district},Bihar,IN",
        "appid": api_key,
        "units": "metric" # Returns temperature in Celsius
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        
        # Handle the specific case where the LLM passes an invalid district name
        if response.status_code == 404:
             return json.dumps({
                 "status": "error", 
                 "message": f"District '{district}' not recognized by the weather database."
             })
             
        response.raise_for_status()
        data = response.json()

        # We want to extract a clean 3-day summary for the LLM context.
        forecast_summary = {}
        
        for item in data.get("list", []):
            # dt_txt format: "2024-06-12 12:00:00"
            date_str = item["dt_txt"].split(" ")[0]
            time_str = item["dt_txt"].split(" ")[1]
            
            # Grab the mid-day forecast (e.g., 09:00 or 12:00) as the representative daily weather
            if date_str not in forecast_summary and time_str >= "09:00:00":
                forecast_summary[date_str] = {
                    "temperature_c": item["main"]["temp"],
                    "condition": item["weather"][0]["description"].title(),
                    "humidity_percent": item["main"]["humidity"],
                    # pop is 'Probability of Precipitation' (0 to 1). We convert to percentage.
                    "rain_probability_percent": int(item.get("pop", 0) * 100) 
                }
                
            # Stop parsing once we have compiled exactly 3 days
            if len(forecast_summary) == 3:
                break
                
        if not forecast_summary:
             return json.dumps({"status": "error", "message": "Could not parse forecast data."})

        return json.dumps({
            "district": district.title(),
            "forecast": forecast_summary
        })

    except requests.exceptions.RequestException as e:
        return json.dumps({"status": "error", "message": f"Weather API connection failed: {str(e)}"})

# ==========================================
# EXPORT LIST
# ==========================================
mausam_tools_list = [kosi_gandak_flood_alert_api, imd_district_weather]