from typing import Any, Dict, List, Optional, Union, Callable
import json
from ..model.data_format import DataFormat

class DataFormatConverter:
    """Serwis do konwersji danych między różnymi formatami"""
    
    @staticmethod
    def convert(data: Any, source_format: DataFormat, target_format: DataFormat) -> Any:
        """Konwertuje dane z jednego formatu do drugiego"""
        # Jeśli formaty są takie same, zwróć dane bez zmian
        if source_format == target_format:
            return data
            
        # Najpierw konwertuj do formatu pośredniego (LIST)
        if source_format != DataFormat.LIST:
            data = DataFormatConverter._to_list(data, source_format)
            
        # Następnie konwertuj z listy do docelowego formatu
        if target_format != DataFormat.LIST:
            return DataFormatConverter._from_list(data, target_format)
            
        return data
    
    @staticmethod
    def _to_list(data: Any, source_format: DataFormat) -> List[Dict[str, Any]]:
        """Konwertuje dane z określonego formatu na listę słowników"""
        if source_format == DataFormat.LIST:
            return data
            
        elif source_format == DataFormat.JSON:
            try:
                if isinstance(data, str):
                    return json.loads(data)
                return data  # Zakładamy, że dane są już zdekodowane
            except Exception as e:
                raise ValueError(f"Błąd konwersji z JSON: {str(e)}")
                
        elif source_format == DataFormat.DATAFRAME:
            try:
                import pandas as pd
                if isinstance(data, pd.DataFrame):
                    return data.to_dict(orient='records')
                return data  # Jeśli to nie DataFrame, zwróć dane bez zmian
            except ImportError:
                raise ImportError("Biblioteka pandas jest wymagana do konwersji DataFrame")
                
        elif source_format == DataFormat.NDARRAY:
            try:
                import numpy as np
                if isinstance(data, np.ndarray):
                    if data.ndim == 1:
                        return [{"value": x} for x in data]
                    elif data.ndim == 2:
                        return [dict(zip(range(data.shape[1]), row)) for row in data]
                    else:
                        raise ValueError(f"Konwersja z ndarray o wymiarze {data.ndim} nie jest obsługiwana")
                return data
            except ImportError:
                raise ImportError("Biblioteka numpy jest wymagana do konwersji ndarray")
                
        raise ValueError(f"Nieobsługiwany format źródłowy: {source_format}")
    
    @staticmethod
    def _from_list(data: List[Dict[str, Any]], target_format: DataFormat) -> Any:
        """Konwertuje listę słowników do określonego formatu"""
        if target_format == DataFormat.LIST:
            return data
            
        elif target_format == DataFormat.JSON:
            try:
                return json.dumps(data)
            except Exception as e:
                raise ValueError(f"Błąd konwersji do JSON: {str(e)}")
                
        elif target_format == DataFormat.DATAFRAME:
            try:
                import pandas as pd
                return pd.DataFrame(data)
            except ImportError:
                raise ImportError("Biblioteka pandas jest wymagana do konwersji do DataFrame")
                
        elif target_format == DataFormat.NDARRAY:
            try:
                import numpy as np
                return np.array([list(item.values()) for item in data])
            except ImportError:
                raise ImportError("Biblioteka numpy jest wymagana do konwersji do ndarray")
            except Exception as e:
                raise ValueError(f"Błąd konwersji do ndarray: {str(e)}")
                
        raise ValueError(f"Nieobsługiwany format docelowy: {target_format}")
