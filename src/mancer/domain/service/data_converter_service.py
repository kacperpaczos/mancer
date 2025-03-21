from typing import Any, Dict, List, Optional, Union, Callable
import json
from ..model.data_format import DataFormat

class DataFormatConverter:
    """Serwis do konwersji danych między różnymi formatami"""
    
    @staticmethod
    def convert(data: Any, source_format: DataFormat, target_format: DataFormat) -> Optional[Any]:
        """Konwertuje dane z jednego formatu do drugiego"""
        # Jeśli formaty są takie same, zwróć dane bez zmian
        if source_format == target_format:
            return data
            
        # Najpierw konwertuj do formatu pośredniego (LIST)
        if source_format != DataFormat.LIST:
            intermediate_data = DataFormatConverter._to_list(data, source_format)
            if intermediate_data is None:
                return None
            data = intermediate_data
            
        # Następnie konwertuj z listy do docelowego formatu
        if target_format != DataFormat.LIST:
            return DataFormatConverter._from_list(data, target_format)
            
        return data
    
    @staticmethod
    def _to_list(data: Any, source_format: DataFormat) -> Optional[List[Dict[str, Any]]]:
        """Konwertuje dane z określonego formatu na listę słowników"""
        if source_format == DataFormat.LIST:
            return data
            
        elif source_format == DataFormat.JSON:
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except Exception:
                    return None
            return data  # Zakładamy, że dane są już zdekodowane
                
        elif source_format == DataFormat.DATAFRAME:
            try:
                import pandas as pd
                if isinstance(data, pd.DataFrame):
                    return data.to_dict(orient='records')
                return data  # Jeśli to nie DataFrame, zwróć dane bez zmian
            except ImportError:
                return None
                
        elif source_format == DataFormat.NDARRAY:
            try:
                import numpy as np
                if isinstance(data, np.ndarray):
                    if data.ndim == 1:
                        return [{"value": x} for x in data]
                    elif data.ndim == 2:
                        return [dict(zip(range(data.shape[1]), row)) for row in data]
                    else:
                        return None
                return data
            except ImportError:
                return None
                
        return None
    
    @staticmethod
    def _from_list(data: List[Dict[str, Any]], target_format: DataFormat) -> Optional[Any]:
        """Konwertuje listę słowników do określonego formatu"""
        if target_format == DataFormat.LIST:
            return data
            
        elif target_format == DataFormat.JSON:
            try:
                return json.dumps(data)
            except Exception:
                return None
                
        elif target_format == DataFormat.DATAFRAME:
            try:
                import pandas as pd
                return pd.DataFrame(data)
            except ImportError:
                return None
                
        elif target_format == DataFormat.NDARRAY:
            try:
                import numpy as np
                return np.array([list(item.values()) for item in data])
            except (ImportError, Exception):
                return None
                
        return None
