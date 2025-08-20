import os
import requests
import numpy as np
from typing import List
from app.logger import logger
from app.config import settings

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
EMBED_MODEL = settings.EMBED_MODEL

class EmbeddingService:
    """Embedding işlemlerini yöneten servis sınıfı"""
    
    def __init__(self):
        self.model = os.getenv("EMBED_MODEL", "bge-m3")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Metni embedding vektörüne çevirir"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=20
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            return np.array(embedding, dtype=np.float32)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Embedding API hatası: {e}")
    
    def embedding_to_vector_string(self, embedding: np.ndarray) -> str:
        """NumPy array'i PostgreSQL vector formatına çevirir"""
        return "[" + ",".join(f"{x:.6f}" for x in embedding.tolist()) + "]"
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """İki vektör arasındaki cosine similarity hesaplar"""
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        
        return dot_product / (norm_vec1 * norm_vec2)


# Global instance (singleton pattern)
embedding_service = EmbeddingService()

# Convenience functions
def embed(text: str) -> np.ndarray:
    try:
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=20
        )
        r.raise_for_status()
        vec = np.array(r.json().get("embedding"), dtype=np.float32)
        if vec.size == 0:
            raise ValueError("Empty embedding from ollama")
        return vec
    except Exception as e:
        logger.error("Embedding error: %s", e)
        raise

def embedding_to_vector_str(embedding: np.ndarray) -> str:
    """Kısa kullanım için wrapper fonksiyon"""
    return embedding_service.embedding_to_vector_string(embedding)