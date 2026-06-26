import time
import json
import streamlit as st
from datetime import datetime
import sys
import os

# Add the project root to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your LangGraph backend
from src.graph import app
from src.state import KrishiMitraState

# ==========================================
# 1. PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Krishi-Mitra | AI Expert Network",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CRAZY-LEVEL CUSTOM CSS (Glassmorphism & Light Green Theme)
# ==========================================
st.markdown("""
<style>
    /* Global Theme & Background */
    :root {
        --primary-green: #2e7d32;
        --light-green: #e8f5e9;
        --accent-glow: #81c784;
        --bg-color: #f4f9f5;
        --text-main: #1b3a20;
        --glass-bg: rgba(255, 255, 255, 0.65);
        --glass-border: rgba(255, 255, 255, 0.2);
    }
    
    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(circle at 100% 0%, #e8f5e9 0%, transparent 50%),
                          radial-gradient(circle at 0% 100%, #c8e6c9 0%, transparent 50%);
        background-attachment: fixed;
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
    }

    /* Top Navigation Bar Simulation */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Sidebar - Glassmorphism */
    [data-testid="stSidebar"] {
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid var(--glass-border);
    }
    
    /* Headers & Titles */
    h1, h2, h3 {
        color: var(--primary-green);
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    /* Chat Bubbles Animation & Styling */
    [data-testid="stChatMessage"] {
        background: white;
        border-radius: 16px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(46, 125, 50, 0.1);
        animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
        transform: translateY(10px);
    }
    
    /* Specific styling for Assistant vs User */
    [data-testid="stChatMessage"][data-baseweb="flex"]:nth-child(even) {
        background: var(--light-green);
        border: 1px solid var(--accent-glow);
    }

    /* Animations */
    @keyframes slideUp {
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(129, 199, 132, 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(129, 199, 132, 0); }
        100% { box-shadow: 0 0 0 0 rgba(129, 199, 132, 0); }
    }

    /* Status & Online Indicators */
    .agent-status {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        background: white;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        transition: transform 0.2s;
    }
    .agent-status:hover {
        transform: translateX(4px);
    }
    .status-dot {
        height: 10px; width: 10px;
        background-color: #4caf50;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        animation: pulse 2s infinite;
    }

    /* Quick Action Buttons */
    .stButton > button {
        background: white;
        color: var(--primary-green);
        border: 1px solid var(--accent-glow);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .stButton > button:hover {
        background: var(--primary-green);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.2);
    }

    /* Custom Spinner/Status */
    [data-testid="stStatusWidget"] {
        background: white;
        border-radius: 12px;
        border: 1px solid var(--accent-glow);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE MANAGEMENT
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(datetime.now().timestamp())

# ==========================================
# 4. SIDEBAR: AGENT NETWORK DASHBOARD
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/11494/11494106.png", width=60) # Placeholder Leaf Icon
    st.title("Krishi-Mitra")
    st.caption("Bihar Agricultural Intelligence")
    st.markdown("---")
    
    st.subheader("📡 Active Agent Network")
    agents = [
        ("Bhoomi", "Land & Registry"), ("Mausam", "Weather & Floods"), 
        ("Beej", "Seeds & Subsidies"), ("Yojana", "Schemes & DBT"),
        ("Fasal", "Agronomy & NPK"), ("Keet", "Pest & Disease"),
        ("Sinchai", "Irrigation"), ("Pashupalan", "Dairy & Vet"),
        ("Rin", "KCC & Finance"), ("SupplyChain", "Storage & CHC")
    ]
    
    # Render animated agent status indicators
    for agent, role in agents:
        st.markdown(f"""
            <div class="agent-status">
                <span class="status-dot"></span>
                <div>
                    <div>{agent}</div>
                    <div style="font-size: 0.7rem; color: #666; font-weight: 400;">{role}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.caption("System Status: Optimal 🟢")
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.trace_logs = []
        st.session_state.session_id = str(datetime.now().timestamp())
        st.rerun()

# ==========================================
# 5. MAIN LAYOUT (Chat Interface & Analytics)
# ==========================================
# We split the screen: 70% for chat, 30% for real-time LangGraph execution tracing
col_chat, col_trace = st.columns([7, 3])

with col_chat:
    st.header("🚜 Multi-Agent Assistant")
    st.markdown("Ask natural language questions. The Supervisor will route your request to the correct specialist.")
    
    # Quick Action Chips
    st.write("✨ **Suggested Queries:**")
    q_cols = st.columns(4)
    if q_cols[0].button("Kosi Water Level"):
        st.session_state.current_prompt = "What is the current flood status and water level of the Kosi river in Saharsa?"
    if q_cols[1].button("KCC Limit"):
        st.session_state.current_prompt = "Calculate my KCC loan limit for 2.5 acres of Paddy."
    if q_cols[2].button("Disease Check"):
        st.session_state.current_prompt = "My wheat leaves have yellow powder stripes. What pesticide should I use?"
    if q_cols[3].button("Makhana Storage"):
        st.session_state.current_prompt = "Find cold storage for Makhana in Darbhanga."

    st.markdown("<br>", unsafe_allow_html=True)

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍🌾" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Handle Input (From typing or from Quick Action Chips)
    prompt = st.chat_input("Describe your agricultural issue...")
    if "current_prompt" in st.session_state:
        prompt = st.session_state.current_prompt
        del st.session_state.current_prompt # Clear after use

    # ==========================================
    # 6. GRAPH EXECUTION & ROUTING
    # ==========================================
    if prompt:
        # 1. Append & Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(prompt)

        # 2. Display Assistant Response with Animation
        with st.chat_message("assistant", avatar="🤖"):
            # The Status Widget acts as our "thinking" indicator
            with st.status("Initializing Supervisor Agent...", expanded=True) as status_box:
                start_time = time.time()
                
                # Configuration for LangGraph memory (if implemented)
                config = {"configurable": {"thread_id": st.session_state.session_id}}
                
                try:
                    # Stream the graph execution to show real-time routing
                    final_response = ""
                    active_agent = "Supervisor"
                    
                    st.write("↳ Analyzing intent...")
                    
                    # Instead of .invoke(), we use .stream() to catch the agent transitions
                    for event in app.stream({"messages": [("user", prompt)]}, config):
                        for node_name, node_data in event.items():
                            active_agent = node_name
                            st.write(f"↳ Routed to **{node_name}** Agent...")
                            
                            # Log the trace for the sidebar analytics
                            st.session_state.trace_logs.append({
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "node": node_name,
                                "action": "Processing Request"
                            })
                            
                            if "messages" in node_data:
                                final_response = node_data["messages"][-1].content

                    exec_time = round(time.time() - start_time, 2)
                    status_box.update(label=f"✅ Request processed by {active_agent} in {exec_time}s", state="complete", expanded=False)
                    
                    # Display the final output
                    st.markdown(f"**[{active_agent}]**\n\n{final_response}")
                    st.session_state.messages.append({"role": "assistant", "content": f"**[{active_agent}]**\n\n{final_response}"})
                    
                except Exception as e:
                    status_box.update(label="❌ Error in Agent Network", state="error")
                    st.error(f"Graph Execution Failed: {str(e)}")

# ==========================================
# 7. TRACE & ANALYTICS PANE
# ==========================================
with col_trace:
    st.subheader("⚙️ Execution Trace")
    st.markdown("Real-time LangGraph routing logic.")
    
    # A beautiful container for logs
    with st.container(height=600):
        if not st.session_state.trace_logs:
            st.info("Awaiting interaction...")
        else:
            for log in reversed(st.session_state.trace_logs):
                st.markdown(f"""
                <div style="background: white; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid var(--primary-green); font-size: 0.85rem; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                    <span style="color: #888;">{log['time']}</span><br>
                    <strong>Node:</strong> {log['node']}<br>
                    <span style="color: var(--primary-green);">{log['action']}</span>
                </div>
                """, unsafe_allow_html=True)