from typing import Dict, Any
from backend.agents.planner import create_plan
from backend.agents.executor import execute_tasks
from backend.agents.critic import critique_and_improve
from backend.memory.memory import memory_db
import time

class NeuroOrchestrator:
    def __init__(self):
        self.history = []

    def run(self, goal: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Create Plan
        print("🧠 Planning phase...")
        plan = create_plan(goal)
        
        # 2. Execute Tasks
        print("️ Execution phase...")
        execution_results = execute_tasks(plan)
        
        # Aggregate results into a single string for the critic
        aggregated_output = "\n\n".join([
            f"Task: {r['task']}\nResult: {r['result']}" 
            for r in execution_results
        ])
        
        # 3. Critic / Reflection
        print("🔍 Reflection phase...")
        final_output = critique_and_improve(aggregated_output, goal)
        
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