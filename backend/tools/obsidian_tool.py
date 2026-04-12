import os
import re
from datetime import datetime
from typing import List, Optional

class ObsidianTool:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.expanduser(vault_path)
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"Obsidian Vault not found at: {self.vault_path}")

    def _find_note_path(self, note_name: str) -> Optional[str]:
        """Helper to find a note path by name (fuzzy match)."""
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md') and note_name.lower() in file.lower():
                    return os.path.join(root, file)
        return None

    def search_notes(self, query: str, limit: int = 5) -> List[str]:
        matches = []
        query_lower = query.lower()
        for root, _, files in os.walk(self.vault_path):
            if '.git' in root: continue
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query_lower in content.lower() or query_lower in file.lower():
                                matches.append(path)
                                if len(matches) >= limit: return matches
                    except Exception: continue
        return matches

    def read_note(self, note_name: str) -> str:
        path = self._find_note_path(note_name)
        if not path: return f"Note '{note_name}' not found."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def create_note(self, title: str, content: str = "", tags: List[str] = None) -> str:
        """
        Creates a new note. 
        IMPROVEMENT: If content is empty, it creates a placeholder.
        Also handles sanitization better.
        """
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        filename = f"{safe_title}.md"
        path = os.path.join(self.vault_path, filename)
        
        # Handle empty content gracefully
        if not content or content.strip() == "":
            content = "# TODO: Add content here\n\n(This note was created by NeuroOps but no content was provided.)"
        
        date = datetime.now().strftime("%Y-%m-%d")
        tag_str = "\n".join([f"  - {t}" for t in tags]) if tags else ""
        
        header = f"""---
created: {date}
tags:
{tag_str}
---

"""
        full_content = header + content
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            return f"✅ Created note: [[{safe_title}]]\nPath: {path}"
        except Exception as e:
            return f"❌ Failed to create note: {str(e)}"

    def append_to_note(self, note_name: str, content: str) -> str:
        path = self._find_note_path(note_name)
        if not path:
            # If not found, maybe try to create it?
            return f"Error: Note '{note_name}' not found. Try 'create_note' first."
            
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## Update from NeuroOps ({datetime.now().strftime('%H:%M')})\n{content}")
        return f"✅ Updated note: [[{os.path.basename(path)}]]"