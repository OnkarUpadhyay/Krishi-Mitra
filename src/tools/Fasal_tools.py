import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. NPK FERTILIZER CALCULATOR
# ==========================================
class FertilizerCalcInput(BaseModel):
    crop_name: str = Field(description="The crop being planted (e.g., Paddy, Wheat, Maize, Sugarcane, Lentils).")
    area_acre: float = Field(description="Total land area in acres.")

@tool("npk_fertilizer_calculator", args_schema=FertilizerCalcInput)
def npk_fertilizer_calculator(crop_name: str, area_acre: float) -> str:
    """
    Calculates the exact commercial fertilizer requirement (Urea, DAP, MOP) in kilograms 
    based on the specific crop and total acreage.
    Use this when a farmer asks how much fertilizer they need to buy for their field.
    """
    crop = crop_name.lower()
    
    # Standard NPK requirement in kg per acre for major Bihar crops
    # Format: {"crop": (N, P, K)}
    npk_baselines = {
        "paddy": (48, 24, 16),
        "wheat": (40, 20, 16),
        "maize": (48, 24, 16),
        "sugarcane": (60, 34, 24),
        "lentils": (8, 20, 8),   # Legumes fix their own nitrogen, so N is low
        "makhana": (24, 16, 8)   # Aquatic crop, lower chemical requirement
    }
    
    # Default to a generic baseline if crop is not explicitly listed
    req_n, req_p, req_k = npk_baselines.get(crop, (30, 15, 15))
    
    # Scale to farmer's acreage
    total_n = req_n * area_acre
    total_p = req_p * area_acre
    total_k = req_k * area_acre
    
    # AGRONOMIC MATH: Converting pure N, P, K into commercial fertilizer bags
    # DAP (Di-ammonium Phosphate) contains 46% P and 18% N
    # Urea contains 46% N
    # MOP (Muriate of Potash) contains 60% K
    
    # 1. Calculate DAP needed to fulfill the Phosphorus requirement
    dap_kg = total_p / 0.46
    
    # 2. DAP also provides some Nitrogen, so we subtract that from the total N needed
    n_from_dap = dap_kg * 0.18
    remaining_n = max(0, total_n - n_from_dap)
    
    # 3. Calculate Urea needed to fulfill the remaining Nitrogen requirement
    urea_kg = remaining_n / 0.46
    
    # 4. Calculate MOP needed to fulfill the Potassium requirement
    mop_kg = total_k / 0.60
    
    return json.dumps({
        "crop": crop_name.title(),
        "area_acres": area_acre,
        "pure_nutrient_requirement_kg": {
            "Nitrogen (N)": round(total_n, 2),
            "Phosphorus (P)": round(total_p, 2),
            "Potassium (K)": round(total_k, 2)
        },
        "commercial_fertilizer_to_buy_kg": {
            "Urea (46% N)": round(urea_kg, 2),
            "DAP (18% N, 46% P)": round(dap_kg, 2),
            "MOP (60% K)": round(mop_kg, 2)
        },
        "advisory": "Apply full dose of DAP and MOP at the time of sowing. Split Urea into 2-3 top dressings during the crop cycle."
    })

# ==========================================
# 2. SOIL HEALTH CARD ANALYZER
# ==========================================
class SoilHealthInput(BaseModel):
    ph_level: float = Field(description="The pH level of the soil (e.g., 6.5).")
    nitrogen_status: str = Field(description="Status of Nitrogen (Low, Medium, High).")
    phosphorus_status: str = Field(description="Status of Phosphorus (Low, Medium, High).")
    potassium_status: str = Field(description="Status of Potassium (Low, Medium, High).")

@tool("soil_health_card_analyzer", args_schema=SoilHealthInput)
def soil_health_card_analyzer(ph_level: float, nitrogen_status: str, phosphorus_status: str, potassium_status: str) -> str:
    """
    Analyzes the user's Soil Health Card parameters to provide immediate remediation advice.
    Use this when a farmer provides their soil testing results or complains about poor soil quality.
    """
    advisories = []
    
    # Evaluate pH (Acidity/Alkalinity)
    if ph_level < 6.0:
        advisories.append(f"Soil is acidic (pH {ph_level}). Apply Agricultural Lime (Calcium Carbonate) before sowing to neutralize acidity and improve nutrient uptake.")
    elif ph_level > 7.5:
        advisories.append(f"Soil is alkaline/saline (pH {ph_level}). Apply Gypsum and increase organic manure usage to balance the soil pH.")
    else:
        advisories.append(f"Soil pH ({ph_level}) is optimal for most crops.")
        
    # Evaluate Macronutrients
    n_stat = nitrogen_status.lower()
    p_stat = phosphorus_status.lower()
    k_stat = potassium_status.lower()
    
    if n_stat == "low":
        advisories.append("Nitrogen is deficient. Increase Urea application by 25% above the standard recommendation, or incorporate green manure (like Dhaincha).")
    
    if p_stat == "low":
        advisories.append("Phosphorus is deficient. Ensure basal application of DAP or SSP at sowing; do not broadcast later.")
        
    if k_stat == "low":
        advisories.append("Potassium is deficient. Apply MOP to improve crop disease resistance and grain weight.")
        
    if n_stat == "high" and p_stat == "high" and k_stat == "high":
        advisories.append("Macronutrients are abundant. Reduce chemical fertilizer usage by 20% to save costs and prevent soil toxicity.")

    return json.dumps({
        "soil_status_summary": "Analyzed",
        "actionable_advisory": advisories
    })

# ==========================================
# 3. CROP OPTIMIZATION
# ==========================================

class CropOptimizationInput(BaseModel):
    district: str = Field(description="The district in Bihar (e.g., Munger, Purnia).")
    land_area_acre: float = Field(description="Total land area available in acres.")

@tool("land_allocation_optimizer", args_schema=CropOptimizationInput)
def land_allocation_optimizer(district: str, land_area_acre: float) -> str:
    """
    Dynamically fetches the agro-climatic zone, soil type, and current recommended cash crops 
    for a specific district, then calculates a strategic profit vs. fertility matrix.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY missing."

    search = TavilySearchResults(max_results=2, tavily_api_key=api_key)
    query = f"Bihar {district} agro-climatic zone soil type main cash crops fertility management official ICAR"
    
    try:
        results = search.invoke({"query": query})
        if not results:
            return json.dumps({"status": "error", "message": f"Could not retrieve agricultural profile for {district}."})
        context = " ".join([item.get('content', '') for item in results])
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Search failed: {str(e)}"})

    estimated_intensive_revenue = 60000 * land_area_acre
    estimated_sustainable_revenue = 35000 * land_area_acre
    
    return json.dumps({
        "location": district.title(),
        "total_area_acres": land_area_acre,
        "live_agro_climatic_data": context,
        "financial_projections_inr": {
            "intensive_cash_crop_strategy": {
                "estimated_gross": round(estimated_intensive_revenue, 2),
                "soil_impact": "High Depletion. Will require significant chemical fertilizer offset."
            },
            "sustainable_intercropping_strategy": {
                "estimated_gross": round(estimated_sustainable_revenue, 2),
                "soil_impact": "Neutral/Positive. Legumes or green manure will fix nitrogen."
            }
        },
        "system_instruction": "Read the 'live_agro_climatic_data'. Identify the specific soil type and 2 suitable crops for this district. Then, present the user with a final recommendation balancing the financial projections with the soil impact."
    })

# ==========================================
# EXPORT LIST
# ==========================================
fasal_tools_list = [npk_fertilizer_calculator, soil_health_card_analyzer, land_allocation_optimizer]