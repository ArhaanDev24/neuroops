from backend.llm import generate_response

def critique_and_improve(output: str, original_goal: str) -> str:
    """
    Reviews the final output against the original goal and improves it.
    """
    prompt = f"""
    Original Goal: "{original_goal}"
    
    Current Output:
    {output}
    
    Act as a Senior Quality Assurance Engineer.
    1. Critique the output: Is it accurate? Complete? Clear?
    2. Rewrite the output to perfectly satisfy the original goal.
    
    Provide only the improved final output.
    """
    
    return generate_response(prompt)