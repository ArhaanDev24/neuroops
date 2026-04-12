from backend.llm import generate_response, structured_output
from backend.tools.python_tool import execute_python
from backend.tools.file_tool import read_file, write_file
import json

class CodeArchitect:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def solve_coding_task(self, task_description: str, context: str = "") -> str:
        """
        Iteratively writes, executes, and fixes code until the task is solved.
        """
        current_code = ""
        last_error = ""
        
        system_prompt = """
        You are an expert Senior Software Engineer. 
        Your goal is to write Python code to solve the user's task.
        
        Rules:
        1. Analyze the task and previous errors carefully.
        2. Output valid, runnable Python code.
        3. If you need to read existing files, mention them in your thought process, but the final output must be the code block.
        4. Do not include markdown fences like ```python in your raw code output if possible, but standard practice is okay if parsed correctly.
        """

        for attempt in range(self.max_retries):
            print(f"   🤖 Coding Attempt {attempt + 1}/{self.max_retries}...")

            # Construct Prompt
            prompt = f"""
            Task: {task_description}
            
            Context (Previous attempts/errors):
            {last_error if last_error else "No previous errors. Start fresh."}
            
            Current Project Files (Read if needed):
            {context}

            Please provide the COMPLETE Python code to solve this task. 
            If fixing an error, explain briefly what changed, then provide the full corrected code.
            """

            # Get Code from LLM
            raw_response = generate_response(prompt, system_prompt)
            
            # Extract code block (simple regex)
            code_match = re.search(r'```python\n(.*?)\n```', raw_response, re.DOTALL)
            if not code_match:
                code_match = re.search(r'```\n(.*?)\n```', raw_response, re.DOTALL)
            
            if code_match:
                current_code = code_match.group(1).strip()
            else:
                # Fallback: assume whole response is code if no fences found
                current_code = raw_response.strip()

            # Execute Code
            # We save it as 'neuroops_temp_script.py' so the agent can reference it if needed
            result = execute_python(current_code, save_as="neuroops_temp_script.py")

            if "Execution Failed" not in result and "Error" not in result.split('\n')[0]:
                return f"✅ Success!\nCode:\n{current_code}\n\nOutput:\n{result}"
            
            # Update error context for next loop
            last_error = f"Attempt {attempt + 1} failed with:\n{result}"
            
            # Optional: Store the failed attempt in memory for learning
            from backend.memory.memory import memory_db
            memory_db.store_memory(f"Coding Task: {task_description}\nFailed Code: {current_code}\nError: {result}", {"type": "coding_failure"})

        return f"❌ Failed to solve task after {self.max_retries} attempts.\nFinal Error:\n{last_error}"

# Helper to extract code from LLM response
import re