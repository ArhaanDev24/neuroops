import chromadb
from typing import List, Optional
import uuid
import os

class MemorySystem:
    def __init__(self, persist_directory: str = "./chroma_db"):
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "neuroops_memory"
        
        # Try to get existing collection, otherwise create it
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # Collection does not exist, so we create it
            self.collection = self.client.create_collection(self.collection_name)

    def store_memory(self, text: str, metadata: Optional[dict] = None):
        """Stores text into long-term memory."""
        doc_id = str(uuid.uuid4())
        # Ensure metadata is a dict, not None, to avoid ChromaDB issues
        safe_metadata = metadata if metadata is not None else {}
        
        self.collection.add(
            documents=[text],
            metadatas=[safe_metadata],
            ids=[doc_id]
        )

    def retrieve_memory(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieves relevant context based on query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

# Singleton instance
memory_db = MemorySystem()