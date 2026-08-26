import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, Any

class SemanticCache:
    def __init__(self, threshold: float = 0.95, model_name: str = "all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.dimension = 384
        # IndexFlatIP with normalized vectors calculates Cosine Similarity directly
        self.index = faiss.IndexFlatIP(self.dimension)
        self.entries = []  # Stores [{"prompt": str, "response": str}]
        self.threshold = threshold

    def lookup(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a semantically similar prompt already exists in cache.
        """
        if self.index.ntotal == 0:
            return None

        query_vec = self.encoder.encode([prompt], normalize_embeddings=True)
        distances, indices = self.index.search(np.array(query_vec, dtype=np.float32), k=1)

        best_score = float(distances[0][0])
        best_idx = int(indices[0][0])

        if best_score >= self.threshold and best_idx < len(self.entries):
            return {
                "cached": True,
                "response": self.entries[best_idx]["response"],
                "similarity_score": round(best_score, 4),
                "original_prompt": self.entries[best_idx]["prompt"]
            }
        return None

    def store(self, prompt: str, response: str):
        """
        Stores prompt embedding and response text in the FAISS index.
        """
        vec = self.encoder.encode([prompt], normalize_embeddings=True)
        self.index.add(np.array(vec, dtype=np.float32))
        self.entries.append({"prompt": prompt, "response": response})