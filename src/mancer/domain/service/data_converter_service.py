import json
from typing import Any, Optional, Union

import polars as pl

from ..model.data_format import DataFormat


class DataFormatConverter:
    """Service for converting data between formats.

    Provides helpers to convert between CommandResult data formats: POLARS, JSON, TABLE.
    Conversions are performed via POLARS DataFrame as intermediate representation.
    """

    @staticmethod
    def convert(data: Any, source_format: DataFormat, target_format: DataFormat) -> Optional[Union[pl.DataFrame, str]]:
        """Convert data from source_format to target_format using POLARS as intermediate if needed."""
        # Jeśli formaty są takie same, zwróć dane bez zmian
        if source_format == target_format:
            return data

        # Najpierw konwertuj do formatu pośredniego (POLARS)
        if source_format != DataFormat.POLARS:
            intermediate_data = DataFormatConverter._to_polars(data, source_format)
            if intermediate_data is None:
                return None
            data = intermediate_data

        # Następnie konwertuj z POLARS do docelowego formatu
        if target_format != DataFormat.POLARS:
            return DataFormatConverter._from_polars(data, target_format)

        return data

    @staticmethod
    def _to_polars(data: Any, source_format: DataFormat) -> Optional[pl.DataFrame]:
        """Convert data from a specific format to a polars DataFrame."""
        if source_format == DataFormat.POLARS:
            return data if isinstance(data, pl.DataFrame) else None

        elif source_format == DataFormat.JSON:
            if isinstance(data, str):
                try:
                    records = json.loads(data)
                    return pl.DataFrame(records)
                except Exception:
                    return None
            elif isinstance(data, list):
                return pl.DataFrame(data)
            return None

        elif source_format == DataFormat.TABLE:
            # TABLE format is assumed to be string tabular representation
            if isinstance(data, str):
                # Simple parsing - split by newlines and tabs/spaces
                lines = data.strip().split("\n")
                if not lines:
                    return pl.DataFrame()

                # Use first line as headers if it looks like headers
                headers = lines[0].split()
                rows = [line.split() for line in lines[1:] if line.strip()]

                if headers and rows:
                    return pl.DataFrame(rows, schema=headers)
                elif rows:
                    # No headers, use generic column names
                    return pl.DataFrame(rows)
                return None
            return None
        # All DataFormat enum values are handled above

    @staticmethod
    def _from_polars(data: pl.DataFrame, target_format: DataFormat) -> Union[pl.DataFrame, Optional[str]]:
        """Convert polars DataFrame to target format."""
        if target_format == DataFormat.POLARS:
            return data

        elif target_format == DataFormat.JSON:
            try:
                records = data.to_dicts()
                return json.dumps(records, ensure_ascii=False)
            except Exception:
                return None

        elif target_format == DataFormat.TABLE:
            # Simple table representation - tab-separated values
            try:
                return data.write_csv(separator="\t", include_header=True)
            except Exception:
                return None
        # All DataFormat enum values are handled above
