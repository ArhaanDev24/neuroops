from backend.llm import structured_output
from backend.tools import TOOL_REGISTRY
from backend.agents.code_architect import CodeArchitect # Import new agent
from typing import List, Dict, Any
import os

# Initialize the Architect
code_architect = CodeArchitect(max_retries=3)

def select_tool(task: str) -> Dict[str, Any]:
    # Compact tool descriptions
    tools_summary = "; ".join([
        f"{name}({','.join(info['args'])})" 
        for name, info in TOOL_REGISTRY.items()
    ])
    
    schema = '{"tool_name": "string", "arguments": {}}'
    
    # ✅ ENHANCED PROMPT FOR OBSIDIAN & COMPLEX ARGS
    prompt = f"""
    Task: "{task}"
    Tools: {tools_summary}
    
    CRITICAL RULES FOR JSON OUTPUT:
    1. If using 'create_vault_note', you MUST put the FULL note content inside the "content" argument.
    2. Do NOT say "I will write it later". Write it NOW in the JSON.
    3. Escape all newlines as \\n and quotes as \\" inside the JSON string.
    4. If content is too long, summarize it first, then use 'append_to_note' in a subsequent step.
    5. For 'complex_coding', ensure the code string is also properly escaped.
    
    SPECIAL INSTRUCTION:
    - Complex logic/scripting -> 'complex_coding'
    - Simple math -> 'execute_python'
    - Reading files first -> 'read_file' then 'complex_coding'
    
    Return STRICTLY valid JSON only. No markdown fences.
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