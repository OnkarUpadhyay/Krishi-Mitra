from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class KrishiMitraState(TypedDict):
    """
    The global state that is passed between the Supervisor and the 10 Worker Agents.
    """
    
    # The conversation and tool-call history. 
    # 'add_messages' is the built-in LangGraph v1.0+ reducer that automatically 
    # appends new messages to the existing list rather than overwriting it.
    messages: Annotated[list[BaseMessage], add_messages]
    
    # The routing directive. The Supervisor updates this to the name of the 
    # next agent (e.g., "Land", "Weather") or "FINISH" when the task is done.
    next: str
    
    # Tracks which specific worker just completed an action. 
    # Crucial for debugging and ensuring the Supervisor knows who is reporting back.
    sender: str