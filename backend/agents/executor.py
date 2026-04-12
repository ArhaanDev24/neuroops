from backend.llm import structured_output
from backend.tools import TOOL_REGISTRY
from backend.agents.code_architect import CodeArchitect # Import new agent
from typing import List, Dict, Any
import os

# Initialize the Architect
code_architect = CodeArchitect(max_retries=3)

def select_tool(task: str) -> Dict[str, Any]:
    # ... (Keep existing select_tool logic exactly as before) ...
    available_tools_desc = "\n".join([
        f"- {name}: {info['description']} (Args: {', '.join(info['args'])})" 
        for name, info in TOOL_REGISTRY.items()
    ])
    
    schema = '''
    {
        "tool_name": "string (one of: read_file, write_file, web_search, execute_python, complex_coding, or 'none')",
        "arguments": {} 
    }
    '''
    
    prompt = f"""
    Task: "{task}"
    
    Available Tools:
    {available_tools_desc}
    
    SPECIAL INSTRUCTION:
    - If the task requires writing a script, building a feature, debugging, or complex logic spanning multiple lines, select 'complex_coding'.
    - If it's a simple one-line calculation, use 'execute_python'.
    - If it requires reading existing project files first, use 'read_file' then 'complex_coding'.
    
    Return strictly JSON.
    """
    
    decision = structured_output(prompt, schema)
    return decision

def execute_task(task: str) -> Dict[str, Any]:
    decision = select_tool(task)
    tool_name = decision.get("tool_name", "none")
    args = decision.get("arguments", {})
    
    result = ""
    
    if tool_name == "complex_coding":
        #  NEW LOGIC: Use the Code Architect for iterative development
        print("   ️ Engaging Code Architect for complex task...")
        
        # Gather context: List files in current directory to help the agent
        try:
            files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
            context = f"Available files: {', '.join(files)}"
        except:
            context = "Could not list files."
            
        result = code_architect.solve_coding_task(task, context=context)
        tool_name = "complex_coding (Iterative)"

    elif tool_name == "none":
        from backend.llm import generate_response
        result = generate_response(f"Perform the following task directly: {task}")
        
    elif tool_name in TOOL_REGISTRY:
        tool_info = TOOL_REGISTRY[tool_name]
        func = tool_info["func"]
        try:
            filtered_args = {k: v for k, v in args.items() if k in tool_info["args"]}
            result = func(**filtered_args)
        except Exception as e:
            result = f"Tool execution failed: {str(e)}"
    else:
        result = f"Unknown tool requested: {tool_name}"
    
    return {
        "task": task,
        "tool_used": tool_name,
        "result": result
    }

def execute_tasks(tasks: List[str]) -> List[Dict[str, Any]]:
    results = []
    for task in tasks:
        print(f"Executing: {task}...")
        res = execute_task(task)
        results.append(res)
    return results