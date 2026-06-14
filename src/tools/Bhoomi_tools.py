import json
import re
import easyocr
import numpy as np
from langchain.tools import tool
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright

# ==========================================
# 1. JAMABANDI SCRAPING TOOL (PLAYWRIGHT + OCR)
# ==========================================
class JamabandiInput(BaseModel):
    district: str = Field(description="Name of the district in Bihar (e.g., Patna)")
    anchal: str = Field(description="Name of the Anchal (Circle/Block)")
    halka: str = Field(description="Name of the Halka (Panchayat)")
    mauja: str = Field(description="Name of the Mauja (Village)")
    jamabandi_number: str = Field(description="The specific Jamabandi number to look up")

@tool("fetch_bihar_bhumi_jamabandi", args_schema=JamabandiInput)
def fetch_bihar_bhumi_jamabandi(district: str, anchal: str, halka: str, mauja: str, jamabandi_number: str) -> str:
    """
    Fetches the land record (Jamabandi/Register II) details from the Bihar Bhumi portal using headless browser automation.
    Use this when a user asks about their land registry, ownership details, or Khata/Khesra numbers.
    """
    # Note: ASP.NET WebForms dynamically generate IDs. You may need to inspect the live DOM
    # and update the selectors (e.g., 'select#district' might be 'select[name$="ddlDistrict"]')
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Navigate to the portal
            page.goto("https://emutation.bihar.gov.in/biharBhumireport/ViewJamabandi", wait_until="networkidle")
            
            # 2. Select District & Wait for Anchal postback
            page.locator("select#district_selector").select_option(label=district)
            page.wait_for_timeout(1500) 
            
            # 3. Select Anchal & Click Proceed
            page.locator("select#anchal_selector").select_option(label=anchal)
            page.locator("button#btnProceed").click()
            page.wait_for_timeout(2000)
            
            # 4. Select Halka & Mauja
            page.locator("select#halka_selector").select_option(label=halka)
            page.wait_for_timeout(1000)
            page.locator("select#mauja_selector").select_option(label=mauja)
            
            # 5. Choose 'Search by Jamabandi Number' and enter value
            page.locator("input#radio_jamabandi").click()
            page.locator("input#txt_jamabandi_no").fill(jamabandi_number)
            
            # 6. CAPTCHA SOLVER (Math expression: "9 + 5 = ?")
            captcha_answer = 0
            captcha_text_element = page.locator("span#captcha_math")
            
            if captcha_text_element.is_visible():
                # Primary Route: Fast DOM Extraction
                captcha_text = captcha_text_element.inner_text()
                numbers = [int(s) for s in re.findall(r'\d+', captcha_text)]
                if len(numbers) >= 2:
                    captcha_answer = sum(numbers)
            else:
                # Fallback Route: Computer Vision OCR
                # Triggered if the portal updates to a rendered image/canvas
                captcha_img_locator = page.locator("img#captcha_image")
                captcha_img_bytes = captcha_img_locator.screenshot()
                
                reader = easyocr.Reader(['en'], gpu=False) # Set gpu=True if you have CUDA mapped
                result = reader.readtext(np.frombuffer(captcha_img_bytes, np.uint8), detail=0)
                
                extracted_str = "".join(result)
                numbers = [int(s) for s in re.findall(r'\d+', extracted_str)]
                if len(numbers) >= 2:
                    captcha_answer = sum(numbers)

            # Inject the calculated math result
            page.locator("input#txt_captcha_input").fill(str(captcha_answer))
            
            # 7. Execute Search
            page.locator("button#btnSearch").click()
            
            # Wait for the table to render or a javascript alert to pop up
            page.wait_for_selector("table#resultTable", timeout=10000)
            
            # 8. Extract the Row Data
            row = page.locator("table#resultTable tbody tr").nth(0)
            if row.count() == 0:
                browser.close()
                return json.dumps({"status": "error", "message": "No Jamabandi record found."})
                
            cells = row.locator("td").all_inner_texts()
            
            record = {
                "owner_name": cells[1] if len(cells) > 1 else "N/A",
                "khata_no": cells[2] if len(cells) > 2 else "N/A",
                "khesra_no": cells[3] if len(cells) > 3 else "N/A",
                "rakba": cells[4] if len(cells) > 4 else "N/A",
                "jamabandi_no": jamabandi_number
            }
            
            browser.close()
            return json.dumps({"status": "success", "data": record})

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Scraping failed: {str(e)}"})


# ==========================================
# 2. LAND UNIT CONVERTER TOOL
# ==========================================
class UnitConversionInput(BaseModel):
    value: float = Field(description="The numerical value of the land area to convert")
    from_unit: str = Field(description="The unit to convert from (Dhur, Katha, Bigha, Acre, Decimal, SqFt)")
    to_unit: str = Field(description="The unit to convert to (Dhur, Katha, Bigha, Acre, Decimal, SqFt)")

@tool("land_unit_converter", args_schema=UnitConversionInput)
def land_unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """
    Converts regional Bihar land measurement units (Dhur, Katha, Bigha) to standard units (Acre, Decimal, SqFt).
    Use this whenever a user asks to convert land area.
    """
    sqft_conversion_rates = {
        "dhur": 68.0625,
        "katha": 1361.25,
        "bigha": 27225.0,
        "decimal": 435.6,
        "acre": 43560.0,
        "sqft": 1.0
    }
    
    from_u = from_unit.strip().lower()
    to_u = to_unit.strip().lower()
    
    if from_u not in sqft_conversion_rates or to_u not in sqft_conversion_rates:
        return f"Error: Supported units are Dhur, Katha, Bigha, Decimal, Acre, and SqFt. You provided {from_unit} to {to_unit}."
    
    value_in_sqft = value * sqft_conversion_rates[from_u]
    final_value = value_in_sqft / sqft_conversion_rates[to_u]
    
    return f"{value} {from_unit.capitalize()} is equal to {round(final_value, 3)} {to_unit.capitalize()}."

# ==========================================
# 3. PARIMARJAN (RECTIFICATION) ADVISOR
# ==========================================
class ParimarjanInput(BaseModel):
    error_type: str = Field(description="The type of error in the land record (e.g., 'name mistake', 'area mismatch', 'missing jamabandi').")

@tool("parimarjan_document_advisor", args_schema=ParimarjanInput)
def parimarjan_document_advisor(error_type: str) -> str:
    """
    Advises the exact legal documents and affidavits required to fix specific mistakes 
    in Bihar's digitized land records via the Parimarjan portal.
    """
    error = error_type.lower()
    
    # Base requirements for almost all Parimarjan applications
    advisory = {
        "mandatory_documents": [
            "Application form in the prescribed format",
            "Self-attested copy of the current Jamabandi / Rent Receipt",
            "Proof of identity (Aadhar Card)"
        ],
        "specific_requirements": [],
        "action_step": "Submit these compiled documents as a single PDF on the Bihar Bhumi Parimarjan portal."
    }
    
    if any(word in error for word in ["name", "spelling", "father"]):
        advisory["specific_requirements"] = [
            "Registered Sale Deed (Kewala) or Khatiyan showing the correct name.",
            "An affidavit sworn before an Executive Magistrate stating the correct name."
        ]
    elif any(word in error for word in ["area", "rakba", "mismatch", "extent"]):
        advisory["specific_requirements"] = [
            "Copy of the registered deed (Kewala) clearly mentioning the exact area.",
            "Trace map (N नक्शा) of the specific plot.",
            "Order copy of any previous mutation case (if applicable)."
        ]
    elif any(word in error for word in ["missing", "not online", "not showing"]):
        advisory["specific_requirements"] = [
            "Manual rent receipts (Offline Rasid) cut before the digitization process.",
            "Return filed by the Zamindar (if applicable/available)."
        ]
    else:
        advisory["specific_requirements"] = ["Detailed affidavit explaining the specific discrepancy."]
        advisory["action_step"] = "Consult the local Karamchari (Revenue Officer) to verify the required proofs for this specific edge case."

    return json.dumps(advisory)

# ==========================================
# 4. BATAIDARI (SHARECROPPING) SETTLEMENT CALCULATOR
# ==========================================
class BataidariInput(BaseModel):
    total_yield_quintals: float = Field(description="Total harvested crop in quintals.")
    market_price_per_quintal: float = Field(description="Current market selling price per quintal in INR.")
    seed_and_fertilizer_cost: float = Field(description="Total cost of seeds and fertilizer in INR.")
    machinery_labor_cost: float = Field(description="Total cost of tractor rental and labor in INR.")
    landowner_paid_inputs: bool = Field(description="Did the landowner pay for the seeds/fertilizer? (True/False)")
    split_ratio: str = Field(description="The agreed crop split, e.g., '50-50' or '60-40' (Farmer-Landowner).")

@tool("bataidari_settlement_calculator", args_schema=BataidariInput)
def bataidari_settlement_calculator(total_yield_quintals: float, market_price_per_quintal: float, 
                                    seed_and_fertilizer_cost: float, machinery_labor_cost: float, 
                                    landowner_paid_inputs: bool, split_ratio: str) -> str:
    """
    Calculates a fair financial settlement between a sharecropper (Bataidar) and a landowner,
    accounting for who paid the input costs.
    """
    # 1. Calculate Gross Revenue
    gross_revenue = total_yield_quintals * market_price_per_quintal
    
    # 2. Parse Split Ratio (Default to 50/50 if not understood)
    try:
        bataidar_share_pct = int(split_ratio.split('-')[0]) / 100.0
    except:
        bataidar_share_pct = 0.50
        
    landowner_share_pct = 1.0 - bataidar_share_pct
    
    # 3. Calculate Base Split (Before expenses)
    bataidar_base_value = gross_revenue * bataidar_share_pct
    landowner_base_value = gross_revenue * landowner_share_pct
    
    # 4. Adjust for Expenses
    # Typically, the Bataidar pays for machinery/labor.
    # If the Bataidar also paid for seeds/fertilizer but the agreement was that the landowner should share it,
    # we adjust the final cash payout.
    
    if landowner_paid_inputs:
        # Landowner paid for materials, Bataidar paid for labor
        bataidar_net_profit = bataidar_base_value - machinery_labor_cost
        landowner_net_profit = landowner_base_value - seed_and_fertilizer_cost
        settlement_note = "Landowner provided materials. Base split applied to gross revenue, each absorbs their own costs."
    else:
        # Bataidar paid for EVERYTHING. They need to be reimbursed from the gross before the split.
        total_costs = seed_and_fertilizer_cost + machinery_labor_cost
        net_revenue = gross_revenue - total_costs
        
        bataidar_net_profit = (net_revenue * bataidar_share_pct)
        landowner_net_profit = (net_revenue * landowner_share_pct)
        settlement_note = "Bataidar covered all costs. Total expenses were deducted from the gross revenue before calculating the final profit split."

    return json.dumps({
        "gross_harvest_value_inr": round(gross_revenue, 2),
        "bataidar_final_take_home_inr": round(max(bataidar_net_profit, 0), 2),
        "landowner_final_take_home_inr": round(max(landowner_net_profit, 0), 2),
        "financial_logic": settlement_note
    })

# ==========================================
# EXPORT LIST
# ==========================================
# Import this array directly into your graph.py file
bhoomi_tools_list = [
    fetch_bihar_bhumi_jamabandi,
    land_unit_converter,
    parimarjan_document_advisor,
    bataidari_settlement_calculator
]