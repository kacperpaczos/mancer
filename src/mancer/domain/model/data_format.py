from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import json

class DataFormat(Enum):
    """Formaty danych dla structured_output w CommandResult"""
    LIST = auto()  # Standardowa lista słowników/obiektów
    DATAFRAME = auto()  # Pandas DataFrame
    NDARRAY = auto()  # NumPy ndarray
    JSON = auto()  # JSON string
    TABLE = auto()  # Format tabeli (dla komend jak df, ps)
    
    @staticmethod
    def from_string(format_name: str) -> Optional['DataFormat']:
        """Konwertuje string na enum DataFormat"""
        format_map = {
            "list": DataFormat.LIST,
            "dataframe": DataFormat.DATAFRAME,
            "ndarray": DataFormat.NDARRAY,
            "json": DataFormat.JSON,
            "table": DataFormat.TABLE
        }
        
        if format_name.lower() not in format_map:
            return None
            
        return format_map[format_name.lower()]
    
    @staticmethod
    def to_string(format_type: 'DataFormat') -> str:
        """Konwertuje enum DataFormat na string"""
        format_map = {
            DataFormat.LIST: "list",
            DataFormat.DATAFRAME: "dataframe", 
            DataFormat.NDARRAY: "ndarray",
            DataFormat.JSON: "json",
            DataFormat.TABLE: "table"
        }
        
        return format_map.get(format_type, "list")
    
    @staticmethod
    def is_convertible(source_format: 'DataFormat', target_format: 'DataFormat') -> bool:
        """Sprawdza czy konwersja między formatami jest możliwa"""
        # Wszystkie formaty są konwertowalne między sobą
        return True 