from pathlib import Path
import hashlib
import json
import shutil
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class FileInfo:
    path: Path
    hash: str
    content: Dict

class FileManager:
    def calculate_hash(self, file_path: Path) -> str:
        """Oblicza hash pliku"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def load_json(self, file_path: Path) -> Optional[Dict]:
        """Wczytuje zawartość pliku JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
            
    def save_json(self, file_path: Path, data: Dict):
        """Zapisuje dane do pliku JSON"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def copy_file(self, source: Path, destination: Path) -> bool:
        """Kopiuje plik z zachowaniem struktury katalogów"""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            return True
        except Exception:
            return False
            
    def compare_files(self, file1: Path, file2: Path) -> bool:
        """Porównuje zawartość dwóch plików znak po znaku"""
        if not file1.exists() or not file2.exists():
            return False
        
        try:
            with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
                content1 = f1.read()
                content2 = f2.read()
                return content1 == content2
        except Exception:
            return False
            
    def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Pobiera informacje o pliku"""
        try:
            content = self.load_json(file_path)
            if content is None:
                return None
                
            return FileInfo(
                path=file_path,
                hash=self.calculate_hash(file_path),
                content=content
            )
        except Exception:
            return None 