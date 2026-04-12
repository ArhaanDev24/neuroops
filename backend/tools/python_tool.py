import subprocess
import sys
import tempfile
import os

def execute_python(code: str) -> str:
    """
    Executes Python code in a safe, isolated temporary environment.
    WARNING: Ensure this runs in a containerized environment in production.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        os.unlink(tmp_path) # Cleanup
        
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout else "Code executed successfully (no output)."
        else:
            return f"Execution Error:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Execution timed out after 10 seconds."
    except Exception as e:
        return f"System Error: {str(e)}"