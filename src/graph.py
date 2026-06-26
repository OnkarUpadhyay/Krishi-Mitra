import os
from typing import Literal
from pydantic import BaseModel

from dotenv import load_dotenv
from groq import RateLimitError
from langchain_core.messages import SystemMessage
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver # ADD MEMORYSAVER

from src.tools.Bhoomi_tools import bhoomi_tools_list
from src.tools.Mausam_tools import mausam_tools_list
from src.tools.Beej_tools import beej_tools_list
from src.tools.Yojana_tools import yojana_tools_list
from src.tools.Fasal_tools import fasal_tools_list
from src.tools.Keet_tools import keet_tools_list
from src.tools.Sinchai_tools import sinchai_tools_list
from src.tools.Pashupalan_tools import pashupalan_tools_list
from src.tools.Rin_tools import rin_tools_list
from src.tools.Supply_Chain_tools import supplychain_tools_list
from src.tools.Missing_Data_tools import ask_user_for_missing_data


# Import the state schema we defined earlier
from src.state import KrishiMitraState

load_dotenv()
groq_api_keys = [
    os.getenv("GROQ_API_KEY")
    or os.getenv("GROQ_API_KEY_1")
    or os.getenv("GROQ_API_KEY_2")
    or os.getenv("GROQ_API_KEY_3"),
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
]

groq_api_keys = [api_key for api_key in groq_api_keys if api_key]
groq_api_keys = list(dict.fromkeys(groq_api_keys))

if not groq_api_keys:
    raise RuntimeError("Set GROQ_API_KEY or GROQ_API_KEY_1/GROQ_API_KEY_2/GROQ_API_KEY_3 in .env")

os.environ.setdefault("GROQ_API_KEY", groq_api_keys[0])

groq_llms = [
    ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )
    for api_key in groq_api_keys[:3]
]

# ==========================================
# 1. INITIALIZE LLM
# ==========================================
# Switched to ChatGroq for ultra-low latency inference during multi-agent routing.
# (Ensure your GROQ_API_KEY is set in your .env file)
def invoke_with_groq_fallback(callable_factory):
    last_error = None

    for llm in groq_llms:
        try:
            return callable_factory(llm)
        except RateLimitError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("No Groq clients were configured")


# ==========================================
# 2. WORKER NODE FACTORY 
# ==========================================

def make_worker_node(agent_name: str, tools: list, system_prompt: str):

    safe_tools = tools + [ask_user_for_missing_data]

    groq_safeguard = (
        "CRITICAL INSTRUCTION: If you lack the required parameters to use your main tools, "
        "DO NOT guess. You MUST use the 'ask_user_for_missing_data' tool to ask the user for the missing details."
    )

    full_system_prompt = f"{system_prompt}\n\n{groq_safeguard}"

    def worker_node(state: KrishiMitraState):
        def invoke_worker(llm):
            worker_agent = create_agent(
                model=llm,
                tools=safe_tools,
                system_prompt=SystemMessage(content=full_system_prompt),
                name=agent_name,
            )

            return worker_agent.invoke({"messages": state["messages"]})

        result = invoke_with_groq_fallback(invoke_worker)

        # 3. RETURN: We pass the updated messages back.
        return {"messages": result["messages"], "sender": agent_name}
        
    return worker_node

# ==========================================
# 3. INSTANTIATE ALL 10 WORKERS
# ==========================================

bhoomi_node = make_worker_node(
    "Bhoomi", 
    bhoomi_tools_list, 
    "You are Bhoomi, the Land Agent for Bihar. Handle land disputes, registries, land unit converter, rectification advisory, and Bataidari settlement calculations. If the user does not provide enough specific details (like Khata/Khesra numbers, error types, or split ratios), DO NOT try to guess or use a tool. Just ask the user directly for the missing information."
)

mausam_node = make_worker_node(
    "Mausam", 
    mausam_tools_list, 
    "You are Mausam, the Weather Agent for Bihar. Handle disaster management, flood monitoring, and micro-climate forecasting. If the user asks about the weather or floods but does not provide their specific district or village, ask them explicitly for it before fetching data."
)

beej_node = make_worker_node(
    "Beej", 
    beej_tools_list, 
    "You are Beej, the Seed Agent for Bihar. Handle queries about seed varieties, BRBN availability, and government subsidies. If the user does not specify the crop name or their district, ask them explicitly so you can recommend the right localized variety."
)

yojana_node = make_worker_node(
    "Yojana", 
    yojana_tools_list, 
    "You are Yojana, the Schemes Agent for Bihar. Handle government scheme eligibility, API Setu certificate verification, and application status. If the user does not provide the specific scheme name or their eligibility document ID (like a Ration Card or Caste Certificate number), ask them for it explicitly."
)

fasal_node = make_worker_node(
    "Fasal", 
    fasal_tools_list, 
    "You are Fasal, the Crop & Agronomy Agent for Bihar. Handle NPK fertilizer math, soil health analysis, AND crop selection optimization. If the user asks what to plant to maximize profit or balance soil fertility, use your optimization tool. If they haven't provided their district, crop name, or acreage, ask them for it explicitly before running calculations."
)

keet_node = make_worker_node(
    "Keet", 
    keet_tools_list, 
    "You are Keet, the Pest Agent for Bihar. Handle plant disease diagnosis and pesticide recommendations. If the user complains about a disease but does not describe the specific symptoms (e.g., leaf color, spots, wilting) or the crop name, ask them to describe it clearly before recommending any chemicals."
)

sinchai_node = make_worker_node(
    "Sinchai", 
    sinchai_tools_list, 
    "You are Sinchai, the Irrigation Agent for Bihar. Handle crop water requirements and tube-well subsidies. If the user wants an irrigation calculation but hasn't provided the crop name, soil type (sandy/clay/loam), or land area in acres, ask them for it explicitly."
)

pashupalan_node = make_worker_node(
    "Pashupalan", 
    pashupalan_tools_list, 
    "You are Pashupalan, the Dairy and Livestock Agent for Bihar. Handle livestock health, nutrition, and cooperative dairy networks like Sudha. If the user does not specify the type of animal (e.g., cow, buffalo, goat) or their district, ask them for it explicitly."
)

rin_node = make_worker_node(
    "Rin", 
    rin_tools_list, 
    "You are Rin, the Finance Agent for Bihar. Handle microfinance, Kisan Credit Card (KCC) limit calculations, and crop insurance. If the user asks for a KCC calculation but hasn't provided their crop names, acreage, or the year of the KCC loan, ask them for it explicitly."
)

supplychain_node = make_worker_node(
    "SupplyChain", 
    supplychain_tools_list, 
    "You are SupplyChain, the Logistics Agent for Bihar. Handle cold storage locator and Custom Hiring Center (CHC) machinery rentals. If the user does not provide the commodity they want to store, the specific machinery they need, or their district, ask them explicitly."
)

# ==========================================
# 4. THE SUPERVISOR NODE
# ==========================================

# Define the exact routing options for the LLM output
class Route(BaseModel):
    next: Literal[
        "Bhoomi", "Mausam", "Beej", "Yojana", "Fasal", 
        "Keet", "Sinchai", "Pashupalan", "Rin", "SupplyChain", "FINISH"
    ]

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """You are the Krishi-Mitra Supervisor. Your job is to manage a team of specialized agents for Bihar's agricultural ecosystem.\n
     Given the user's request and the conversation history, decide which worker should act next.\n
     Available Workers:
     - Bhoomi (Land)
     - Mausam (Weather)
     - Beej (Seeds)
     - Yojana (Schemes)
     - Fasal (Crop)
     - Keet (Pest)
     - Sinchai (Irrigation)
     - Pashupalan (Dairy)
     - Rin (Finance)
     - SupplyChain (Logistics)

     CRITICAL ROUTING RULES:
     1. If the user asks a new question, route them to the correct worker.
     2. IF THE LAST MESSAGE IS FROM A WORKER (e.g., they answered the question OR asked the user for missing details like an ID or scheme name), YOU MUST OUTPUT "FINISH".
     3. NEVER route back to a worker if they just spoke. You must output "FINISH" to pause the system and let the user reply.
     
     You must respond in valid JSON format matching exactly this schema:
     {{"next": "WorkerName or FINISH"}}"""),
    MessagesPlaceholder(variable_name="messages"),
])

def supervisor_node(state: KrishiMitraState):
    messages = state["messages"]
    
    valid_workers = [
        "Bhoomi", "Mausam", "Beej", "Yojana", "Fasal", 
        "Keet", "Sinchai", "Pashupalan", "Rin", "SupplyChain"
    ]
    
    if messages:
        last_message = messages[-1]
        
        # NEW LOGIC: Check if the human just replied.
        # BaseMessage objects have a 'type' attribute (e.g., 'human', 'ai', 'tool')
        if last_message.type == "human":
            # The user just provided missing info. Skip the loop breaker and let the LLM route!
            pass 
        else:
            # The last message was NOT human. Check if we need to break the loop.
            last_sender = getattr(last_message, "name", None) or state.get("sender")
            if last_sender in valid_workers:
                return {"next": "FINISH"}

    # 3. OTHERWISE, RUN THE LLM TO ROUTE NEW USER INPUT
    def invoke_supervisor(llm):
        structured_llm = llm.with_structured_output(Route, method="json_mode")
        supervisor_chain = supervisor_prompt | structured_llm
        return supervisor_chain.invoke({"messages": state["messages"]})

    result = invoke_with_groq_fallback(invoke_supervisor)
    return {"next": result.next}

    
# ==========================================
# 6. COMPILE THE FULL 10-AGENT GRAPH
# ==========================================
builder = StateGraph(KrishiMitraState)

# Add all 11 nodes (1 Supervisor + 10 Workers)
builder.add_node("Supervisor", supervisor_node)
builder.add_node("Bhoomi", bhoomi_node)
builder.add_node("Mausam", mausam_node)
builder.add_node("Beej", beej_node)
builder.add_node("Yojana", yojana_node)
builder.add_node("Fasal", fasal_node)
builder.add_node("Keet", keet_node)
builder.add_node("Sinchai", sinchai_node)
builder.add_node("Pashupalan", pashupalan_node)
builder.add_node("Rin", rin_node)
builder.add_node("SupplyChain", supplychain_node)

# Add edges: Every worker ALWAYS reports back to the Supervisor
workers = [
    "Bhoomi", "Mausam", "Beej", "Yojana", "Fasal", 
    "Keet", "Sinchai", "Pashupalan", "Rin", "SupplyChain"
]
for worker in workers:
    builder.add_edge(worker, "Supervisor")

# Add conditional edges: The Supervisor dictates the next move
builder.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Bhoomi": "Bhoomi",
        "Mausam": "Mausam",
        "Beej": "Beej",
        "Yojana": "Yojana",
        "Fasal": "Fasal",
        "Keet": "Keet",
        "Sinchai": "Sinchai",
        "Pashupalan": "Pashupalan",
        "Rin": "Rin",
        "SupplyChain": "SupplyChain",
        "FINISH": END
    }
)

# Set the entry point to the Supervisor
builder.add_edge(START, "Supervisor")

# Initialize the memory saver
memory = MemorySaver()

# Compile into the final LangGraph application
app = builder.compile(checkpointer=memory)
