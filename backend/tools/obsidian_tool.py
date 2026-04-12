import os
import re
from datetime import datetime
from typing import List, Optional

class ObsidianTool:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.expanduser(vault_path)
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"Obsidian Vault not found at: {self.vault_path}")

    def search_notes(self, query: str, limit: int = 5) -> List[str]:
        """
        Searches note content and filenames for a query.
        Returns list of file paths.
        """
        matches = []
        query_lower = query.lower()
        
        for root, _, files in os.walk(self.vault_path):
            # Skip .git or hidden folders
            if '.git' in root: continue
            
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query_lower in content.lower() or query_lower in file.lower():
                                matches.append(path)
                                if len(matches) >= limit:
                                    return matches
                    except Exception:
                        continue
        return matches

    def read_note(self, note_name: str) -> str:
        """Reads a note by filename or partial match."""
        # Simple fuzzy find
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md') and note_name.lower() in file.lower():
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
        return f"Note '{note_name}' not found."

    def create_note(self, title: str, content: str, tags: List[str] = None) -> str:
        """Creates a new note with frontmatter."""
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title) # Sanitize filename
        filename = f"{safe_title}.md"
        path = os.path.join(self.vault_path, filename)
        
        # Generate Frontmatter (YAML)
        date = datetime.now().strftime("%Y-%m-%d")
        tag_str = "\n".join([f"  - {t}" for t in tags]) if tags else ""
        
        header = f"""---
created: {date}
tags:
{tag_str}
---

"""
        full_content = header + content
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        return f"✅ Created note: [[{safe_title}]]"

    def append_to_note(self, note_name: str, content: str) -> str:
        """Appends content to an existing note."""
        # Find file first
        target_path = None
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md') and note_name.lower() in file.lower():
                    target_path = os.path.join(root, file)
                    break
            if target_path: break
            
        if not target_path:
            return f"Error: Note '{note_name}' not found."
            
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## Update from NeuroOps ({datetime.now().strftime('%H:%M')})\n{content}")
            
        return f"✅ Updated note: [[{os.path.basename(target_path)}]]"