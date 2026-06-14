***

```markdown
# 🌾 Krishi-Mitra: Multi-Agent Agricultural Intelligence System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-State_Orchestration-orange.svg)
![Groq](https://img.shields.io/badge/Groq-gpt--oss--120b-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red.svg)

**Krishi-Mitra** is an AI-driven agricultural intelligence system designed to provide localized, real-time farming advisories. By leveraging a hub-and-spoke multi-agent architecture, the system overcomes the fragility of static web scraping and delivers highly accurate, fault-tolerant agricultural support for domains such as supply chain logistics, Kisan Credit Card (KCC) limits, and seed subsidies.

---

## ✨ Key Features

* **Multi-Agent Orchestration:** A central `Supervisor` node intelligently routes user queries to 10+ specialized domain workers (e.g., `SupplyChain`, `Mausam`, `Beej`).
* **Deterministic State Transitions:** Abandons fragile native tool-calling in favor of strictly enforced `json_mode` parsing via Pydantic, ensuring 100% routing stability.
* **Programmatic Safeguards:** Features a built-in deterministic loop-breaker (`ask_user_for_missing_data`) that intercepts incomplete queries and prompts the user for required parameters, completely mitigating API execution crashes.
* **Dynamic Information Retrieval:** Integrates Tavily and DuckDuckGo search pipelines to fetch live, localized agricultural data instead of relying on unstable static government portal scraping.
* **Sub-Second Routing Latency:** Utilizes the Groq API (`openai/gpt-oss-120b`) to execute complex state-graph routing decisions almost instantaneously.

---

## 📂 Project Directory Structure

```text
Krishi_mitra/
├── src/
│   ├── tools/                    # Specialized agent toolsets
│   │   ├── Beej_tools.py         # Seeds & Subsidies data retrieval
│   │   ├── Bhoomi_tools.py       # Land & Registry data
│   │   ├── Fasal_tools.py        # Agronomy & NPK recommendations
│   │   ├── Keet_tools.py         # Pest & Disease diagnostics
│   │   ├── Mandi_tools.py        # Live market prices
│   │   ├── Mausam_tools.py       # Weather & Flood tracking
│   │   ├── Missing_Data_tools.py # Programmatic fallback safeguard
│   │   ├── Pashupalan_tools.py   # Dairy & Veterinary services
│   │   ├── Rin_tools.py          # KCC & Financial limits
│   │   ├── Sinchai_tools.py      # Irrigation logistics
│   │   ├── Supply_Chain_tools.py # Cold Storage & Logistics tracking
│   │   └── Yojana_tools.py       # Government Schemes & DBT
│   ├── app.py                    # Streamlit conversational web interface
│   ├── graph.py                  # LangGraph state-graph & routing logic
│   └── state.py                  # Pydantic state schemas & validation
├── tests/                        # Unit and integration test suites
├── .env                          # API keys (Groq, Tavily, LangSmith)
├── .gitignore                    # Git ignore file
├── .python-version               # Python version specification
├── langgraph.json                # LangGraph Studio configuration
├── main.py                       # CLI entry point / Main execution script
├── requirements.txt              # Project dependencies
└── pyproject.toml                # Project dependencies and metadata

## 🚀 Installation & Setup

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/Krishi-Mitra.git
cd Krishi_mitra
```

**2. Set up the virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r pyproject.toml  # Or use pip install -r requirements.txt
```

**3. Configure Environment Variables:**
Create a `.env` file in the root directory and add your API keys:
```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Krishi_mitra
```

---

## 💻 Usage

**Run the Streamlit Web App:**
To launch the interactive chat interface with real-time LangGraph tracing execution:
```bash
streamlit run src/app.py
```

**Run via CLI / Backend Testing:**
To execute standard queries through the terminal:
```bash
python main.py
```

---

## 🔮 Future Work

- **Acoustic Interfaces:** Integration of STT (Speech-to-Text) and TTS (Text-to-Speech) pipelines to support voice-based queries in regional languages (e.g., Hindi, Bhojpuri).
- **Multimodal Diagnostics:** Integrating computer vision models to detect plant diseases from uploaded images and recommend targeted pesticide applications.
- **Pan-India Scalability:** Expanding data retrieval pipelines beyond state-specific nodes to support nationwide agricultural databases.