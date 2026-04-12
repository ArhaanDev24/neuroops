from backend.llm import structured_output
from typing import List

def create_plan(goal: str) -> List[str]:
    """
    Breaks a high-level goal into a list of actionable steps.
    """
    schema = '{"tasks": ["step 1", "step 2", "..."]}'
    
    prompt = f"""
    Analyze the following goal and break it down into a sequential list of specific, actionable tasks.
    Goal: "{goal}"
    
    Consider which tools might be needed for each step, but focus on the logical flow.
    Return strictly JSON.
    """
    
    response = structured_output(prompt, schema)
    return response.get("tasks", [])