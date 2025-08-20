import json
import pathlib
import os
from typing import List, Dict, Any
from pathlib import Path
from app.logger import logger
from app.config import settings

JSON_PATH = Path(settings.JSON_PATH)

class JSONFileManager:
    """JSON dosya işlemlerini yöneten sınıf"""
    
    def __init__(self):
        self.json_path = settings.JSON_PATH
        self.file_path = pathlib.Path(self.json_path)
    
    def ensure_file_exists(self):
        """JSON dosyasının var olduğundan emin olur, yoksa oluşturur"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")
            logger.debug("JSON file created: %s", self.file_path)
    
    def read_data(self) -> List[Dict[str, Any]]:
        """JSON dosyasını okur ve Python listesi döndürür"""
        try:
            raw = self.file_path.read_text(encoding="utf-8-sig")
            if not raw.strip():
                return []
            data = json.loads(raw)
            logger.debug("JSON read: %s items from %s", len(data), self.file_path)
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.debug("JSON read error: %s - %s", type(e).__name__, str(e))
            return []
    
    def write_data(self, data: List[Dict[str, Any]]):
        """Python listesini JSON dosyasına yazar"""
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
        logger.debug("JSON written: %s items to %s", len(data), self.file_path)
    
    def append_question(self, question_data: Dict[str, Any]):
        """Yeni bir soru ekler"""
        data = self.read_data()
        data.append(question_data)
        self.write_data(data)
        logger.info(
            "JSON appended id=%s path=%s (total: %s items)", 
            question_data.get("id"), self.file_path, len(data)
        )
    
    def remove_question_by_id(self, question_id: int) -> bool:
        """ID'ye göre soru siler, başarılıysa True döndürür"""
        data = self.read_data()
        original_length = len(data)
        data = [item for item in data if item.get("id") != question_id]
        
        if len(data) < original_length:
            self.write_data(data)
            logger.info(
                "JSON removed id=%s path=%s (diff=%s, total: %s items)", 
                question_id, self.file_path, original_length - len(data), len(data)
            )
            return True
        
        logger.debug("JSON remove failed: id=%s not found", question_id)
        return False
    
    def update_question(self, question_id: int, updated_data: Dict[str, Any]) -> bool:
        """ID'ye göre soru günceller, başarılıysa True döndürür"""
        data = self.read_data()
        for i, item in enumerate(data):
            if item.get("id") == question_id:
                data[i].update(updated_data)
                self.write_data(data)
                logger.info(
                    "JSON updated id=%s path=%s", 
                    question_id, self.file_path
                )
                return True
        
        logger.debug("JSON update failed: id=%s not found", question_id)
        return False


# Global instance
json_manager = JSONFileManager()

# Convenience functions
def ensure_json_file():
    """Kısa kullanım için wrapper"""
    json_manager.ensure_file_exists()

def append_question_to_json(question_data: Dict[str, Any]):
    """Kısa kullanım için wrapper"""
    json_manager.append_question(question_data)

def remove_question_from_json(question_id: int) -> bool:
    """Kısa kullanım için wrapper"""
    return json_manager.remove_question_by_id(question_id)