from typing import Any, Dict, List, Optional, Union, Callable
import json
import re
from ..model.data_format import DataFormat

class DataFormatConverter:
    """Service for converting data between formats.

    Provides helpers to convert between CommandResult data formats: LIST, JSON, DATAFRAME, NDARRAY.
    Conversions are performed via a LIST (records) intermediate representation.
    """

    @staticmethod
    def convert(data: Any, source_format: DataFormat, target_format: DataFormat) -> Optional[Any]:
        """Convert data from source_format to target_format using LIST as intermediate if needed."""
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
        """Convert data from a specific format to a list of dict records."""
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
                return json.dumps(data, ensure_ascii=False)
            except Exception:
                return None
                
        elif target_format == DataFormat.DATAFRAME:
            try:
                import pandas as pd
                
                def convert_size(value):
                    """Convert textual values with units and various decimal separators to numeric.

                    Handles units (K/M/G/T) and decimal formats (dot/comma/semicolon).
                    """
                    if not isinstance(value, str):
                        return value
                    
                    # Usuwamy wszystkie spacje
                    cleaned_value = value.strip()
                    
                    # Wykrywamy jednostki miary (K, M, G, T)
                    multipliers = {'K': 1024, 'k': 1024, 'M': 1024**2, 'm': 1024**2, 
                                   'G': 1024**3, 'g': 1024**3, 'T': 1024**4, 't': 1024**4}
                    
                    unit_multiplier = 1
                    for unit, mult in multipliers.items():
                        if cleaned_value.endswith(unit):
                            cleaned_value = cleaned_value[:-1].strip()
                            unit_multiplier = mult
                            break
                    
                    # Replace special characters and percent signs
                    cleaned_value = cleaned_value.replace('%', '').replace('€', '')
                    
                    # Próbujemy wykryć format liczby
                    decimal_separator = '.'
                    thousand_separator = None
                    
                    # Sprawdzamy czy zawiera przecinek
                    if ',' in cleaned_value:
                        # Jeśli jest kropka i przecinek, zakładamy format angielski (1,234.56)
                        if '.' in cleaned_value:
                            decimal_separator = '.'
                            thousand_separator = ','
                        else:
                            # Jeśli jest tylko przecinek, to prawdopodobnie format europejski (1234,56)
                            decimal_separator = ','
                    
                    # Sprawdzamy czy zawiera średnik
                    if ';' in cleaned_value:
                        decimal_separator = ';'
                    
                    # Zastępujemy separator tysięczny na pusty string
                    if thousand_separator:
                        cleaned_value = cleaned_value.replace(thousand_separator, '')
                    
                    # Zastępujemy separator dziesiętny na kropkę
                    if decimal_separator != '.':
                        cleaned_value = cleaned_value.replace(decimal_separator, '.')
                    
                    # Próbujemy przekonwertować
                    try:
                        # Jeśli string wygląda na liczbę, konwertujemy
                        if re.match(r'^-?\d+\.?\d*$', cleaned_value):
                            return float(cleaned_value) * unit_multiplier
                        # Jeśli nie, zwracamy oryginalną wartość
                        return value
                    except:
                        # W przypadku błędu, zwracamy oryginalną wartość
                        return value
                
                # Konwertuj dane
                converted_data = []
                for item in data:
                    converted_item = {}
                    for key, value in item.items():
                        # Próbuj przekonwertować wartości na liczby
                        converted_item[key] = convert_size(value)
                    converted_data.append(converted_item)
                
                return pd.DataFrame(converted_data)
            except ImportError:
                return None
                
        elif target_format == DataFormat.NDARRAY:
            try:
                import numpy as np
                return np.array([list(item.values()) for item in data])
            except (ImportError, Exception):
                return None
                
        return None
