import json
import pathlib
from pathlib import Path
from typing import List
from app.logger import logger
from app.config import settings


class CategoryManager:
    """Kategori yönetimi sınıfı"""
    
    def __init__(self):
        self.categories_path = settings.CATEGORIES_PATH
        self.file_path = pathlib.Path(self.categories_path)
        self.default_categories = ["tahakkuk", "tahsilat", "diger"]
    
    def ensure_file_exists(self):
        """Kategori dosyasının var olduğundan emin olur"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text(
                json.dumps(self.default_categories, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
            logger.debug("Categories file created: %s", self.file_path)
    
    def load_categories(self) -> List[str]:
        """Kategorileri yükler"""
        try:
            if self.file_path.exists():
                raw = self.file_path.read_text(encoding="utf-8-sig").strip()
                if raw:
                    return json.loads(raw)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return self.default_categories.copy()
    
    def save_categories(self, categories: List[str]):
        """Kategorileri kaydeder"""
        self.file_path.write_text(
            json.dumps(categories, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
        logger.debug("Categories saved: %s items", len(categories))
    
    def add_category(self, category: str) -> bool:
        """Yeni kategori ekler, zaten varsa False döndürür"""
        categories = self.load_categories()
        if category not in categories:
            categories.append(category)
            self.save_categories(categories)
            logger.info("Category added: %s (total: %s)", category, len(categories))
            return True
        logger.debug("Category already exists: %s", category)
        return False
    
    def remove_category(self, category: str) -> bool:
        """Kategori siler, başarılıysa True döndürür"""
        categories = self.load_categories()
        if category in categories:
            categories.remove(category)
            self.save_categories(categories)
            logger.info("Category removed: %s (total: %s)", category, len(categories))
            return True
        logger.debug("Category not found for removal: %s", category)
        return False
    
    def category_exists(self, category: str) -> bool:
        """Kategorinin var olup olmadığını kontrol eder"""
        exists = category in self.load_categories()
        logger.debug("Category check: %s -> %s", category, exists)
        return exists


# Global instance
category_manager = CategoryManager()

# Convenience functions
def load_categories() -> List[str]:
    """Kısa kullanım için wrapper"""
    categories = category_manager.load_categories()
    logger.debug("Categories loaded: %s items", len(categories))
    return categories

def ensure_categories_file():
    """Kısa kullanım için wrapper"""
    category_manager.ensure_file_exists()

def add_category_if_new(category: str) -> bool:
    """Kısa kullanım için wrapper"""
    return category_manager.add_category(category)