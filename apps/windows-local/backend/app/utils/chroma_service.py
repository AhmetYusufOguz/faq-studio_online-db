import chromadb
import numpy as np
from typing import List, Dict, Any, Optional
from app.logger import logger
from app.config import settings
import os

class ChromaService:
    """ChromaDB ile vektör arama servisi"""
    
    def __init__(self):
        # ChromaDB path'ini environment'dan al veya default kullan
        # chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        # self.client = chromadb.PersistentClient(path=chroma_path)
        chroma_path = settings.CHROMA_DB_PATH
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name="faq_questions",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity kullan
        )
        self.embedding_model = None
        logger.info(f"ChromaDB initialized at {chroma_path}")
    
    def initialize_embeddings(self, embedding_function):
        """Embedding fonksiyonunu ayarla"""
        self.embedding_model = embedding_function
        logger.info("Embedding function set for ChromaDB")
    
    
    def add_question(self, question_id: int, question: str, answer: str, 
                keywords: str, category: str, embedding: List[float]):
        """Soru ekler - çift eklemeyi önler"""
        try:
            # Daha güvenli bir şekilde var olup olmadığını kontrol et
            existing = self.collection.get(ids=[str(question_id)], include=[])
            if existing and existing['ids'] and str(question_id) in existing['ids']:
                if settings.DEBUG:
                    logger.debug("Question %s already exists in ChromaDB, skipping", question_id)
                return False  # Eklenmedi
            
            metadata = {
                "id": str(question_id),
                "answer": answer,
                "keywords": keywords,
                "category": category
            }
            
            self.collection.add(
                ids=[str(question_id)],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[question]
            )
            
            logger.debug("Question added to ChromaDB: id=%s", question_id)
            return True  # Eklendi
            
        except Exception as e:
            logger.error("Error adding question %s to ChromaDB: %s", question_id, e)
            return False
    
    def search_similar(self, query_embedding: List[float], top_k: int = 3, 
                      threshold: float = 0.7):
        """Benzer soruları ara"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"]
            )
            
            # Mesafeleri benzerlik skoruna dönüştür (1 - distance)
            similar_questions = []
            if results["metadatas"] and results["metadatas"][0]:
                for i, (metadata, document, distance) in enumerate(zip(
                    results["metadatas"][0],
                    results["documents"][0],
                    results["distances"][0]
                )):
                    similarity = 1 - distance  # Cosine distance -> similarity
                    if similarity >= threshold:
                        similar_questions.append({
                            "id": int(metadata["id"]),
                            "question": document,
                            "answer": metadata["answer"],
                            "keywords": metadata["keywords"],
                            "category": metadata["category"],
                            "sim": similarity
                        })
            
            return similar_questions
        except Exception as e:
            logger.error("ChromaDB search error: %s", e)
            return []
    
    def delete_question(self, question_id: int):
        """Soru sil"""
        try:
            self.collection.delete(ids=[str(question_id)])
            logger.debug("Question deleted from ChromaDB: id=%s", question_id)
        except Exception as e:
            logger.error("ChromaDB delete error: %s", e)
    
    def get_all_questions(self):
        """Tüm soruları getir"""
        try:
            return self.collection.get()
        except Exception as e:
            logger.error("ChromaDB get all error: %s", e)
            return {}

# Global instance
chroma_service = ChromaService()