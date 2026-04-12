import subprocess
import sys
import os
import tempfile
import re

def execute_python(code: str, save_as: str = None, install_deps: list = None) -> str:
    """
    Executes Python code with advanced capabilities:
    1. Saves code to a file if 'save_as' is provided.
    2. Installs missing packages if 'install_deps' is provided.
    3. Captures stdout and stderr for debugging.
    """
    
    # 1. Handle Dependencies
    if install_deps:
        try:
            print(f"Installing dependencies: {', '.join(install_deps)}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + install_deps, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            return f"Failed to install dependencies: {str(e)}"

    # 2. Prepare Script File
    if save_as:
        # Ensure directory exists
        dir_name = os.path.dirname(save_as)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        script_path = save_as
    else:
        # Use temp file for one-off execution
        fd, script_path = tempfile.mkstemp(suffix='.py')
        os.close(fd)

    try:
        # Write code to file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Execute
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60, # Increased timeout for complex tasks
            cwd=os.getcwd() # Run in current project directory
        )

        output = ""
        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout else "Code executed successfully (no output)."
        else:
            # Return both stdout and stderr for the Critic/Planner to analyze
            output = f"Execution Failed:\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
        
        return output

    except subprocess.TimeoutExpired:
        return "Execution timed out after 60 seconds. The code might be stuck in an infinite loop."
    except Exception as e:
        return f"System Error: {str(e)}"
    finally:
        # Only delete if it was a temp file
        if not save_as and os.path.exists(script_path):
            try:
                os.unlink(script_path)
            except:
                pass