from backend.llm import structured_output
from backend.tools import TOOL_REGISTRY
from backend.agents.code_architect import CodeArchitect # Import new agent
from typing import List, Dict, Any, Optional
import os

class ConsoleLogger:
    def log(self, agent: str, message: str, level: str = "info", is_code: bool = False):
        prefix = "🔍" if level == "info" else ("❌" if level == "error" else "✅")
        print(f"{prefix} [{agent}] {message}")
    
    def request_approval(self, message: str):
        print(f"️ [USER] {message} (Approval skipped)")
        return True

# Initialize the Architect
code_architect = CodeArchitect(max_retries=3)

def select_tool(task: str) -> Dict[str, Any]:
    # Compact tool descriptions
    tools_summary = "; ".join([
        f"{name}({','.join(info['args'])})" 
        for name, info in TOOL_REGISTRY.items()
    ])
    
    schema = '{"tool_name": "string", "arguments": {}}'
    
    # ✅ UPDATED PROMPT WITH OBSIDIAN GUARDRAILS
    prompt = f"""
    Task: "{task}"
    Tools: {tools_summary}
    
    🚨 CRITICAL DECISION RULES:
    1. OBSIDIAN TOOLS ('create_vault_note', 'append_to_note'):
       - ONLY use these if the user EXPLICITLY says: "save", "write to note", "store", "log", or "remember".
       - IF the user is just chatting, saying hello, or asking a question WITHOUT asking to save -> SELECT 'none'.
       - DO NOT save casual conversation.
    
    2. JSON FORMATTING (If using create_vault_note):
       - You MUST put the FULL note content inside the "content" argument.
       - Escape newlines as \\n and quotes as \\".
       - Do NOT say "I will write later". Write NOW.

    3. OTHER TOOLS:
       - Complex logic/scripting -> 'complex_coding'
       - Simple math -> 'execute_python'
       - Reading files first -> 'read_file' then 'complex_coding'

    📝 EXAMPLES:
    - User: "Hello" -> Tool: 'none'
    - User: "What is 2+2?" -> Tool: 'none' (or 'execute_python')
    - User: "Save this summary to a note called 'Summary'" -> Tool: 'create_vault_note'
    - User: "Write my thoughts on AI to vault" -> Tool: 'create_vault_note'
    
    Return STRICTLY valid JSON only. No markdown fences.
    """
    
    decision = structured_output(prompt, schema)
    return decision

def execute_task(task: str, logger: Optional[object] = None) -> Dict[str, Any]:
    local_logger = logger or ConsoleLogger()
    
    decision = select_tool(task)
    tool_name = decision.get("tool_name", "none")
    args = decision.get("arguments", {})
    
    result = ""
    
    # ✅ SAFETY GUARDRAIL: Prevent accidental Obsidian saves for casual chat
    if tool_name in ["create_vault_note", "append_to_note"]:
        lower_task = task.lower()
        
        # Keywords that indicate a SAVE request
        save_keywords = ["save", "write", "store", "log", "note", "vault", "remember", "create"]
        # Keywords that indicate pure CHAT (no save intended)
        chat_keywords = ["hello", "hi", "hey", "how are you", "what is", "who is", "define", "explain"]
        
        has_save_intent = any(k in lower_task for k in save_keywords)
        has_chat_intent = any(k in lower_task for k in chat_keywords)
        
        # If it looks like chat but NO save keyword was found, BLOCK IT
        if has_chat_intent and not has_save_intent:
            local_logger.log("SafetyGuard", f" Blocked accidental save for chat task: '{task}'", level="info")
            tool_name = "none"  # Force fallback to normal chat
            args = {}           # Clear arguments to prevent errors

    if tool_name == "complex_coding":
        # NEW LOGIC: Use the Code Architect for iterative development
        print("   ⚙️ Engaging Code Architect for complex task...")
        
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

def execute_tasks(tasks: List[str], logger: Optional[object] = None) -> List[Dict[str, Any]]:
    # Use the provided logger or fallback to ConsoleLogger
    local_logger = logger or ConsoleLogger()
    
    results = []
    for task in tasks:
        # Log the start of the task using the injected logger
        local_logger.log("Executor", f"Starting task: {task}", level="info")
        
        # Pass the logger down to execute_task
        res = execute_task(task, logger=local_logger)
        
        results.append(res)
        
        # Log the result (truncated if too long)
        preview = str(res['result'])[:100] + "..." if len(str(res['result'])) > 100 else res['result']
        local_logger.log("Executor", f"Task completed: {preview}", level="success")
        
    return results