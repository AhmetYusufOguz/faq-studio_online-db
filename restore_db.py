# restore_db.py
import json
import numpy as np
from app.db import get_conn
from app.utils.embeddings import embed, embedding_to_vector_str
from app.logger import logger

def restore_from_json():
    """JSON'daki soruları veritabanına geri yükler"""
    try:
        # JSON dosyasını oku
        with open('/app/data/questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        logger.info(f"Found {len(questions)} questions in JSON file")
        
        with get_conn() as conn, conn.cursor() as cur:
            inserted_count = 0
            for question in questions:
                try:
                    # Embedding hesapla
                    logger.debug(f"Processing question ID {question['id']}")
                    vec = embed(question['question'])
                    vec_str = embedding_to_vector_str(vec)
                    
                    # Veritabanına ekle
                    cur.execute(
                        "INSERT INTO questions (id, question, answer, keywords, category, embedding, created_by) "
                        "VALUES (%s, %s, %s, %s, %s, %s::vector, %s) "
                        "ON CONFLICT (id) DO NOTHING",
                        (
                            question['id'],
                            question['question'],
                            question['answer'],
                            question['keywords'],
                            question['category'],
                            vec_str,
                            question.get('created_by', 'anonymous')
                        )
                    )
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing question ID {question['id']}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Restored {inserted_count} questions to database")
            
    except Exception as e:
        logger.error(f"Restore error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    restore_from_json()