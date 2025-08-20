import json
import pathlib
import os
from typing import List, Dict, Any


class JSONFileManager:
    """JSON dosya işlemlerini yöneten sınıf"""
    
    def __init__(self):
        self.json_path = os.getenv("JSON_PATH", "/app/data/questions.json")
        self.file_path = pathlib.Path(self.json_path)
    
    def ensure_file_exists(self):
        """JSON dosyasının var olduğundan emin olur, yoksa oluşturur"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")
    
    def read_data(self) -> List[Dict[str, Any]]:
        """JSON dosyasını okur ve Python listesi döndürür"""
        try:
            raw = self.file_path.read_text(encoding="utf-8-sig")
            if not raw.strip():
                return []
            return json.loads(raw)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def write_data(self, data: List[Dict[str, Any]]):
        """Python listesini JSON dosyasına yazar"""
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
    
    def append_question(self, question_data: Dict[str, Any]):
        """Yeni bir soru ekler"""
        data = self.read_data()
        data.append(question_data)
        self.write_data(data)
    
    def remove_question_by_id(self, question_id: int) -> bool:
        """ID'ye göre soru siler, başarılıysa True döndürür"""
        data = self.read_data()
        original_length = len(data)
        data = [item for item in data if item.get("id") != question_id]
        
        if len(data) < original_length:
            self.write_data(data)
            return True
        return False
    
    def update_question(self, question_id: int, updated_data: Dict[str, Any]) -> bool:
        """ID'ye göre soru günceller, başarılıysa True döndürür"""
        data = self.read_data()
        for i, item in enumerate(data):
            if item.get("id") == question_id:
                data[i].update(updated_data)
                self.write_data(data)
                return True
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