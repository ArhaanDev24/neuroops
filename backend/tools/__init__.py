from .file_tool import read_file, write_file
from .web_tool import search_web
from .python_tool import execute_python

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