import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env file
load_dotenv() 

from .file_tool import read_file, write_file
from .web_tool import search_web
from .python_tool import execute_python

# Import Obsidian Tool
try:
    from .obsidian_tool import ObsidianTool
    
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
    
    if vault_path:
        obsidian_agent = ObsidianTool(vault_path)
        OBSIDIAN_TOOLS = {
            "search_vault": {
                "func": obsidian_agent.search_notes,
                "description": "Searches your Obsidian vault for relevant notes.",
                "args": ["query"]
            },
            "read_vault_note": {
                "func": obsidian_agent.read_note,
                "description": "Reads a specific note from your vault.",
                "args": ["note_name"]
            },
            "create_vault_note": {
                "func": obsidian_agent.create_note,
                "description": "Creates a new markdown note in your vault with tags.",
                "args": ["title", "content", "tags"]
            }
        }
    else:
        OBSIDIAN_TOOLS = {}
        print("⚠️ OBSIDIAN_VAULT_PATH not set in .env. Obsidian tools disabled.")

except ImportError:
    OBSIDIAN_TOOLS = {}
except FileNotFoundError as e:
    OBSIDIAN_TOOLS = {}
    print(f"️ Obsidian Error: {e}. Check your path in .env.")

TOOL_REGISTRY = {
    "read_file": {
        "func": read_file,
        "description": "Read content from a local file path.",
        "args": ["path"]
    },
    "write_file": {
        "func": write_file,
        "description": "Write content to a local file path.",
        "args": ["path", "content"]
    },
    "web_search": {
        "func": search_web,
        "description": "Search the web for information.",
        "args": ["query"]
    },
    "execute_python": {
        "func": execute_python,
        "description": "Execute Python code snippet.",
        "args": ["code"]
    }
}

# Merge Obsidian tools into the main registry
TOOL_REGISTRY.update(OBSIDIAN_TOOLS)