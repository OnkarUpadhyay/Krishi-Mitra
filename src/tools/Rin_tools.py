import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# ==========================================
# 1. KCC LOAN LIMIT CALCULATOR
# ==========================================
class KCCDynamicInput(BaseModel):
    crop_area_map: dict = Field(description="Dictionary where key is crop name and value is area in acres (e.g., {'paddy': 2.5, 'wheat': 1.0}).")
    year_of_kcc: int = Field(description="The year of the KCC (1 for first year, up to 5).")
    term_loan_component: float = Field(description="Estimated term loan requirement for machinery/allied activities, if any.")

@tool("kisan_credit_card_calculator", args_schema=KCCDynamicInput)
def kisan_credit_card_calculator(crop_area_map: dict, year_of_kcc: int, term_loan_component: float) -> str:
    """
    Calculates the dynamic KCC limit using official RBI guidelines, incorporating cropping patterns, 
    year-wise cost escalation, and term loan requirements.
    """
    # Dynamic Scale of Finance (SoF) per acre for Bihar (District-specific SoF would be more precise)
    sof_per_acre = {
        "paddy": 35000, "wheat": 32000, "maize": 40000, 
        "makhana": 75000, "vegetables": 60000, "lentils": 25000
    }
    
    # 1. Calculate base cultivation cost for all crops
    total_cultivation_cost = 0
    for crop, area in crop_area_map.items():
        cost = sof_per_acre.get(crop.lower(), 30000)
        total_cultivation_cost += (cost * area)
    
    # 2. Add mandated components (10% Consumption + 20% Maintenance)
    first_year_limit = total_cultivation_cost * 1.30
    
    # 3. Calculate dynamic limit based on KCC year (10% escalation per year from 2nd year onwards)
    if year_of_kcc > 1:
        # Escalation applies to the cultivation portion (the 130% is based on 1st year)
        # Simplified escalation: 1st Year Limit * (1 + 0.10)^(year - 1)
        current_year_limit = first_year_limit * ((1.10) ** (year_of_kcc - 1))
    else:
        current_year_limit = first_year_limit
        
    # 4. Total Permissible Limit (TPL) includes the Term Loan component
    total_permissible_limit = current_year_limit + term_loan_component
    
    return json.dumps({
        "year": year_of_kcc,
        "cultivation_limit": round(current_year_limit, 2),
        "term_loan_component": term_loan_component,
        "total_kcc_limit": round(total_permissible_limit, 2),
        "advisory": "This is an estimate. Final limit is subject to the District Level Technical Committee (DLTC) Scale of Finance and bank assessment."
    })
# ==========================================
# 2. SCHEME & LOAN ELIGIBILITY SEARCH
# ==========================================
class LoanSearchInput(BaseModel):
    query_topic: str = Field(description="The financial topic (e.g., 'Jeevika SHG loan', 'crop insurance claim', 'interest subvention').")

@tool("bihar_finance_search_api", args_schema=LoanSearchInput)
def bihar_finance_search_api(query_topic: str) -> str:
    """
    Searches for official eligibility rules and application processes for Bihar-specific agricultural loans, 
    Jeevika SHG (Self Help Group) loans, and PMFBY crop insurance.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY not found."

    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    query = f"Bihar agriculture finance {query_topic} official eligibility application process Jeevika PACS Bank"
    
    try:
        results = search.invoke({"query": query})
        formatted_reports = [f"Source {i+1} ({item.get('url')}):\n{item.get('content')}" for i, item in enumerate(results)]
        return f"Official Financial Advisories for {query_topic}:\n\n" + "\n\n".join(formatted_reports)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

rin_tools_list = [kisan_credit_card_calculator, bihar_finance_search_api]