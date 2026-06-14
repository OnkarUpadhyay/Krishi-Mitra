import os
import json
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# ==========================================
# 1. THE LOCAL TAXONOMY DATABASE
# ==========================================
# This dictionary structure is infinitely scalable. You can easily move this 
# into a separate 'data/bihar_diseases.json' file later to keep the code clean.
BIHAR_CROP_DISEASE_DB = {
    "maize": [
        {
            "keywords": ["hole", "whorl", "caterpillar", "ragged"],
            "diagnosis": "Fall Armyworm (Spodoptera frugiperda)",
            "severity": "High (Rapid Spread)",
            "chemical": "Spray Emamectin Benzoate 5% SG @ 0.4 g/liter of water.",
            "cultural": "Apply dry sand mixed with lime inside leaf whorls."
        },
        {
            "keywords": ["rot", "smell", "stalk", "wilt"],
            "diagnosis": "Bacterial Stalk Rot",
            "severity": "High",
            "chemical": "Apply Bleaching powder @ 6 kg/acre along with irrigation.",
            "cultural": "Improve field drainage; avoid waterlogging."
        }
    ],
    "paddy": [
        {
            "keywords": ["dead heart", "whitehead", "bore", "worm"],
            "diagnosis": "Yellow Stem Borer (Scirpophaga incertulas)",
            "severity": "High",
            "chemical": "Apply Cartap Hydrochloride 4% GR @ 7.5 kg/acre.",
            "cultural": "Clip seedling tips before transplanting."
        },
        {
            "keywords": ["brown", "spot", "leaf", "lesion"],
            "diagnosis": "Brown Spot (Helminthosporium oryzae)",
            "severity": "Medium",
            "chemical": "Spray Mancozeb 75% WP @ 2.5 g/liter of water.",
            "cultural": "Ensure balanced nitrogen and adequate potassium application."
        }
    ],
    "wheat": [
        {
            "keywords": ["yellow", "stripe", "powder", "rust"],
            "diagnosis": "Yellow Rust (Puccinia striiformis)",
            "severity": "High (Epidemic Potential)",
            "chemical": "Spray Propiconazole 25% EC @ 1 ml/liter immediately.",
            "cultural": "Use rust-resistant varieties like HD 2967."
        },
        {
            "keywords": ["black", "ear", "smut", "powder in grain"],
            "diagnosis": "Loose Smut",
            "severity": "Medium",
            "chemical": "Seed treatment with Carboxin 75% WP @ 2.5 g/kg seed before sowing.",
            "cultural": "Rogue out and destroy infected earheads."
        }
    ],
    "mustard": [
        {
            "keywords": ["aphid", "black bug", "sap", "sticky"],
            "diagnosis": "Mustard Aphid",
            "severity": "High",
            "chemical": "Spray Dimethoate 30% EC @ 1 ml/liter of water.",
            "cultural": "Early sowing in October helps avoid peak aphid populations."
        }
    ],
    "potato": [
        {
            "keywords": ["blight", "black spot", "decay", "water soaked"],
            "diagnosis": "Late Blight (Phytophthora infestans)",
            "severity": "Critical",
            "chemical": "Spray Metalaxyl 8% + Mancozeb 64% WP @ 2.5 g/liter.",
            "cultural": "Use healthy, certified seed tubers; ensure good earthing up."
        }
    ],
    "litchi": [
        {
            "keywords": ["crack", "worm", "borer", "hole in fruit"],
            "diagnosis": "Litchi Fruit Borer",
            "severity": "Medium",
            "chemical": "Spray Novaluron 10% EC @ 1.5 ml/liter 15 days before ripening.",
            "cultural": "Bag fruit bunches early and dispose of fallen fruits."
        }
    ],
    "mango": [
        {
            "keywords": ["hopper", "sticky", "honey dew", "black mold"],
            "diagnosis": "Mango Hopper",
            "severity": "High",
            "chemical": "Spray Imidacloprid 17.8% SL @ 0.3 ml/liter before flowering.",
            "cultural": "Prune dense canopies to allow sunlight and aeration."
        }
    ],
    "gram": [ # Chickpea
        {
            "keywords": ["pod", "caterpillar", "hole", "eat"],
            "diagnosis": "Gram Pod Borer (Helicoverpa armigera)",
            "severity": "High",
            "chemical": "Spray Quinalphos 25% EC @ 2 ml/liter of water.",
            "cultural": "Install bird perches and pheromone traps in the field."
        }
    ],
    "sugarcane": [
        {
            "keywords": ["red", "rot", "sour", "smell", "pith"],
            "diagnosis": "Red Rot (Colletotrichum falcatum)",
            "severity": "Critical (Cancer of Sugarcane)",
            "chemical": "Fungicides are mostly ineffective. Seed treatment with Carbendazim 50% WP @ 1g/liter.",
            "cultural": "Uproot and burn infected clumps. Rotate with non-host crops."
        }
    ],
    "banana": [
        {
            "keywords": ["yellow", "wilt", "skirt", "panama"],
            "diagnosis": "Panama Wilt",
            "severity": "High",
            "chemical": "Soil drenching with Carbendazim 50% WP @ 2g/liter of water.",
            "cultural": "Avoid planting suckers from infected fields."
        }
    ],
    "tomato": [
        {
            "keywords": ["blight", "early", "brown spot", "concentric"],
            "diagnosis": "Early Blight",
            "severity": "Medium",
            "chemical": "Spray Mancozeb @ 2.5g/liter of water.",
            "cultural": "Avoid overhead irrigation; use mulching."
        },
        {
            "keywords": ["wilt", "yellow", "drooping", "bacterial"],
            "diagnosis": "Bacterial Wilt",
            "severity": "High",
            "chemical": "Soil drenching with Copper Oxychloride @ 3g/liter.",
            "cultural": "Practice 3-year crop rotation; use resistant varieties."
        }
    ],
    "lentil": [
        {
            "keywords": ["wilt", "dry", "shrivel", "root rot"],
            "diagnosis": "Wilt / Root Rot",
            "severity": "High",
            "chemical": "Seed treatment with Carbendazim + Mancozeb (2g/kg seed).",
            "cultural": "Ensure well-drained soil; avoid continuous lentil cropping."
        }
    ],
    "onion": [
        {
            "keywords": ["purple", "blotch", "spot", "leaf"],
            "diagnosis": "Purple Blotch",
            "severity": "Medium",
            "chemical": "Spray Mancozeb @ 2.5g/liter or Tebuconazole @ 1ml/liter.",
            "cultural": "Maintain adequate spacing for aeration."
        }
    ],
    "garlic": [
        {
            "keywords": ["thrips", "white streaks", "curled", "silver"],
            "diagnosis": "Thrips",
            "severity": "High",
            "chemical": "Spray Fipronil 5% SC @ 2ml/liter of water.",
            "cultural": "Use blue sticky traps to monitor adult population."
        }
    ],
    "brinjal": [
        {
            "keywords": ["shoot", "fruit", "borer", "hole", "droop"],
            "diagnosis": "Shoot and Fruit Borer",
            "severity": "Critical",
            "chemical": "Spray Spinosad 45% SC @ 0.3 ml/liter.",
            "cultural": "Remove and destroy infested shoots/fruits immediately."
        }
    ],
    "cauliflower": [
        {
            "keywords": ["web", "caterpillar", "leaf", "holes"],
            "diagnosis": "Diamondback Moth",
            "severity": "High",
            "chemical": "Spray Novaluron 10% EC @ 1ml/liter.",
            "cultural": "Intercrop with mustard to act as a trap crop."
        },
        {
            "keywords": ["rot", "black", "soft", "foul smell"],
            "diagnosis": "Black Rot",
            "severity": "Medium",
            "chemical": "Spray Copper Oxychloride @ 3g/liter.",
            "cultural": "Use disease-free seeds; practice crop rotation."
        }
    ],
    "chilli": [
        {
            "keywords": ["leaf curl", "shriveled", "yellowing", "stunted"],
            "diagnosis": "Leaf Curl (Viral)",
            "severity": "High",
            "chemical": "Control vectors (Thrips/Whitefly) using Imidacloprid @ 0.5ml/liter.",
            "cultural": "Uproot and bury severely infected plants to prevent viral spread."
        }
    ]
}

# ==========================================
# 2. OFFLINE SYMPTOM-BASED CLASSIFIER
# ==========================================
class DiseaseDiagnosisInput(BaseModel):
    crop_name: str = Field(description="The affected crop (e.g., Maize, Paddy, Wheat, Litchi, Mustard).")
    symptoms: str = Field(description="Visual symptoms described by the user (e.g., 'holes in leaves', 'dead heart', 'yellow powder').")

@tool("symptom_based_disease_diagnosis", args_schema=DiseaseDiagnosisInput)
def symptom_based_disease_diagnosis(crop_name: str, symptoms: str) -> str:
    """
    Diagnoses plant diseases in Bihar based on a description of the symptoms using a local taxonomy database.
    Use this FIRST before searching the web.
    """
    crop_key = crop_name.strip().lower()
    symp = symptoms.lower()
    
    # Check if the crop exists in our database
    if crop_key in BIHAR_CROP_DISEASE_DB:
        crop_diseases = BIHAR_CROP_DISEASE_DB[crop_key]
        
        # Iterate through the known diseases for this crop
        for disease in crop_diseases:
            # If any of the defining keywords are found in the user's symptom description
            if any(keyword in symp for keyword in disease["keywords"]):
                return json.dumps({
                    "diagnosis": disease["diagnosis"],
                    "severity": disease["severity"],
                    "chemical_recommendation": disease["chemical"],
                    "cultural_control": disease["cultural"]
                })
    
    # If crop is not in DB, or symptoms don't match, trigger the fallback instruction
    return json.dumps({
        "status": "unmatched",
        "message": f"Symptoms '{symptoms}' for {crop_name} did not match the offline taxonomy. Please use the 'kvk_pesticide_search_api' tool to find official recommendations via the web."
    })

# ==========================================
# 3. OFFICIAL KVK / CIBRC SEARCH AGENT
# ==========================================
class PesticideSearchInput(BaseModel):
    crop_name: str = Field(description="The affected crop.")
    pest_disease_name: str = Field(description="The specific name of the pest or disease.")

@tool("kvk_pesticide_search_api", args_schema=PesticideSearchInput)
def kvk_pesticide_search_api(crop_name: str, pest_disease_name: str) -> str:
    """
    Searches the web for official, safe pesticide recommendations.
    Use this if the offline classifier cannot identify the problem.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "System Error: TAVILY_API_KEY not found in environment variables."

    search = TavilySearchResults(max_results=3, tavily_api_key=api_key)
    query = f"{crop_name} {pest_disease_name} control pesticide dosage recommendation Bihar Agricultural University KVK official"
    
    try:
        results = search.invoke({"query": query})
        if not results:
            return json.dumps({"status": "warning", "message": "No official recommendations found."})
            
        formatted_reports = [f"Source {i+1} ({item.get('url', 'Unknown')}):\n{item.get('content', 'No content')}" for i, item in enumerate(results)]
        return f"Official Advisories for {pest_disease_name} on {crop_name}:\n\n" + "\n\n".join(formatted_reports)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tavily Search failed: {str(e)}"})

# ==========================================
# EXPORT LIST
# ==========================================
keet_tools_list = [symptom_based_disease_diagnosis, kvk_pesticide_search_api]