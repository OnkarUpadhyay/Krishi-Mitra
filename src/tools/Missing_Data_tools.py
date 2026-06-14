
from langchain.tools import tool
from pydantic import BaseModel, Field

class AskUserInput(BaseModel):
    question: str = Field(description="The exact question to ask the user to get the missing parameters.")

@tool("ask_user_for_missing_data", args_schema=AskUserInput)
def ask_user_for_missing_data(question: str) -> str:
    """
    CRITICAL ESCAPE HATCH: Use this tool ONLY when you are missing required parameters 
    (like district, acreage, khata number, or crop name) and cannot run your main tools. 
    This tool safely sends your clarifying question to the user.
    """
    return f"System: Successfully asked the user. Wait for their reply."
