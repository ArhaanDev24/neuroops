from backend.llm import structured_output
from backend.tools import TOOL_REGISTRY
from typing import List, Dict, Any

def select_tool(task: str) -> Dict[str, Any]:
    """
    Decides which tool to use for a specific task.
    Returns: {"tool_name": "web_search", "arguments": {"query": "..."}}
    """
    available_tools_desc = "\n".join([
        f"- {name}: {info['description']} (Args: {', '.join(info['args'])})" 
        for name, info in TOOL_REGISTRY.items()
    ])
    
    schema = '''
    {
        "tool_name": "string (one of: read_file, write_file, web_search, execute_python, or 'none' if using LLM reasoning)",
        "arguments": {} 
    }
    '''
    
    prompt = f"""
    Task: "{task}"
    
    Available Tools:
    {available_tools_desc}
    
    If the task requires external data, calculation, or file I/O, select the appropriate tool and provide arguments.
    If the task is purely conversational or creative writing, set tool_name to 'none'.
    """
    
    decision = structured_output(prompt, schema)
    return decision

def execute_task(task: str) -> Dict[str, Any]:
    """
    Executes a single task by selecting a tool and running it.
    """
    # 1. Select Tool
    decision = select_tool(task)
    tool_name = decision.get("tool_name", "none")
    args = decision.get("arguments", {})
    
    result = ""
    
    if tool_name == "none":
        # Fallback to direct LLM generation for non-tool tasks
        from backend.llm import generate_response
        result = generate_response(f"Perform the following task directly: {task}")
    elif tool_name in TOOL_REGISTRY:
        # Execute Tool
        tool_info = TOOL_REGISTRY[tool_name]
        func = tool_info["func"]
        try:
            # Map arguments carefully
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
    """Executes a list of tasks sequentially."""
    results = []
    for task in tasks:
        print(f"Executing: {task}...")
        res = execute_task(task)
        results.append(res)
    return results