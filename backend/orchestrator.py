from typing import Dict, Any, Optional
from backend.agents.planner import create_plan
from backend.agents.executor import execute_tasks
from backend.agents.critic import critique_and_improve
from backend.memory.memory import memory_db
from backend.llm import generate_response
import time

# ✅ Default Console Logger (Fallback for CLI)
class ConsoleLogger:
    def log(self, agent: str, message: str, level: str = "info", is_code: bool = False):
        prefix = "🔍" if level == "info" else ("" if level == "error" else "✅")
        print(f"{prefix} [{agent}] {message}")
    
    def request_approval(self, message: str, task_data: dict = None) -> bool:
        # In CLI mode, we auto-approve or skip interactive prompts
        print(f"⚠️ [USER] {message} (Auto-approved in CLI mode)")
        return True

class NeuroOrchestrator:
    def __init__(self, logger: Optional[object] = None):
        # Use injected logger (from Dashboard) or fallback to ConsoleLogger
        self.logger = logger or ConsoleLogger()
        self.history = []

    def run(self, goal: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # ✅ CHAT DETECTION: Bypass agents for simple greetings/questions
        lower_goal = goal.lower().strip()
        
        # Keywords that trigger direct chat mode
        chat_triggers = ["hello", "hi", "hey", "how are you", "good morning", "good evening", "bye", "thanks", "thank you", "what's up"]
        question_triggers = ["what is", "who is", "define", "explain", "tell me about", "who are you"]
        
        # Keywords that indicate a real task (prevents false positives)
        action_verbs = ["create", "write", "save", "build", "analyze", "search", "code", "fix", "run", "generate", "make", "do"]
        
        has_action = any(v in lower_goal for v in action_verbs)
        is_chat = any(t in lower_goal for t in chat_triggers) or (any(t in lower_goal for t in question_triggers) and not has_action)
        
        if is_chat:
            self.logger.log("System", "Detected casual chat. Skipping planning phase...", level="info")
            final_output = generate_response(f"User said: '{goal}'. Respond naturally, briefly, and helpfully.")
            
            return {
                "goal": goal,
                "plan": ["Direct Response (No Plan Needed)"],
                "execution": [{"task": "Chat", "tool_used": "none", "result": "Replied directly"}],
                "final_output": final_output,
                "duration_seconds": round(time.time() - start_time, 2)
            }

        # 1. Create Plan (Only for real tasks)
        self.logger.log("Planner", f"Analyzing goal: '{goal}'...", level="info")
        plan = create_plan(goal)
        self.logger.log("Planner", f"Generated {len(plan)} steps.", level="success")
        
        # 2. Execute Tasks (Pass logger down!)
        self.logger.log("Executor", "Starting execution loop...", level="info")
        execution_results = execute_tasks(plan, logger=self.logger)
        
        # Aggregate results into a single string for the critic
        aggregated_output = "\n\n".join([
            f"Task: {r['task']}\nResult: {r['result']}" 
            for r in execution_results
        ])
        
        # 3. Critic / Reflection
        self.logger.log("Critic", "Reviewing output for quality...", level="info")
        final_output = critique_and_improve(aggregated_output, goal)
        self.logger.log("Critic", "Reflection complete.", level="success")
        
        # 4. Store Memory
        memory_entry = f"Goal: {goal}\nPlan: {plan}\nOutput: {final_output}"
        memory_db.store_memory(memory_entry, {"goal": goal, "timestamp": time.time()})
        
        end_time = time.time()
        
        return {
            "goal": goal,
            "plan": plan,
            "execution": execution_results,
            "final_output": final_output,
            "duration_seconds": round(end_time - start_time, 2)
        }