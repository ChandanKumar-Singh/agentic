import json
import os
import math
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class Document(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

class SemanticMemory:
    """
    A lightweight Semantic Memory implementation.
    In a full production env, this would wrap ChromaDB/Qdrant/Pinecone.
    Here, to keep it portable, we implement a simple JSON store with basic text overlap/dummy-embedding matching.
    """
    def __init__(self, persistence_path: str = "ai_agent_project/src/memory/chroma_db/store.json"):
        self.persistence_path = persistence_path
        self.documents: List[Document] = []
        self._load()

    def add(self, content: str, metadata: Dict[str, Any] = None):
        """Adds a document to knowledge base."""
        doc = Document(
            id=f"doc_{len(self.documents)+1}_{int(datetime.now().timestamp())}",
            content=content,
            metadata=metadata or {},
            embedding=self._get_embedding(content)
        )
        self.documents.append(doc)
        self._save()
        print(f"Memory: Added document '{content[:30]}...'")

    def retrieve(self, query: str, limit: int = 3) -> List[Document]:
        """
        Retrieves relevant documents. 
        Uses a simple 'Jaccard-like' word overlap for this stateless demo 
        instead of full BERT/OpenAI embeddings to avoid heavy dependencies.
        """
        if not self.documents:
            return []
            
        query_words = set(query.lower().split())
        
        scores = []
        for doc in self.documents:
            doc_words = set(doc.content.lower().split())
            if not doc_words:
                 score = 0
            else:
                 intersection = query_words.intersection(doc_words)
                 score = len(intersection) / len(query_words) if query_words else 0
            
            scores.append((doc, score))
            
        # Sort by score desc
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N with non-zero score
        results = [doc for doc, score in scores if score > 0][:limit]
        print(f"Memory: Retrieved {len(results)} matches for '{query}'")
        return results

    def _get_embedding(self, text: str) -> List[float]:
        # Placeholder for real embedding logic
        return [0.1, 0.2, 0.3] 

    def _save(self):
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        data = [doc.dict() for doc in self.documents]
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f, default=str)

    def _load(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    self.documents = [Document(**d) for d in data]
            except Exception as e:
                print(f"Memory: Failed to load existing store: {e}")
