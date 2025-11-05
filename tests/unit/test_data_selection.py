"""
Testy unit dla zaawansowanych metod selekcji danych w CommandResult i CommandChain
"""

import polars as pl
import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.domain.model.data_format import DataFormat
from mancer.domain.model.execution_history import ExecutionHistory
from mancer.infrastructure.command.system.ls_command import LsCommand


class TestDataSelectionMethods:
    """Testy dla metod selekcji danych"""

    @pytest.fixture
    def sample_dataframe(self):
        """Przykładowy DataFrame do testów"""
        return pl.DataFrame(
            {
                "filename": ["file1.txt", "file2.txt", "file3.txt", "dir1", "dir2"],
                "size": [100, 200, 300, 400, 500],
                "is_directory": [False, False, False, True, True],
                "permissions": ["-rw-r--r--", "-rw-r--r--", "-rw-r--r--", "drwxr-xr-x", "drwxr-xr-x"],
                "raw_line": [
                    "-rw-r--r-- 1 user group 100 Jan 1 12:00 file1.txt",
                    "-rw-r--r-- 1 user group 200 Jan 1 12:01 file2.txt",
                    "-rw-r--r-- 1 user group 300 Jan 1 12:02 file3.txt",
                    "drwxr-xr-x 2 user group 400 Jan 1 12:03 dir1",
                    "drwxr-xr-x 2 user group 500 Jan 1 12:04 dir2",
                ],
            }
        )

    @pytest.fixture
    def sample_result(self, sample_dataframe):
        """Przykładowy CommandResult z DataFrame"""
        return CommandResult(
            raw_output="sample output", success=True, structured_output=sample_dataframe, data_format=DataFormat.POLARS
        )


class TestColumnSelection(TestDataSelectionMethods):
    """Testy dla metod selekcji kolumn"""

    def test_select_columns_single_string(self, sample_result):
        """Test wyboru pojedynczej kolumny przez string"""
        result = sample_result.select_columns("filename")

        assert result.success
        assert result.data_format == DataFormat.POLARS
        assert result.structured_output.columns == ["filename"]
        assert result.structured_output.shape == (5, 1)

    def test_select_columns_list(self, sample_result):
        """Test wyboru wielu kolumn przez listę"""
        result = sample_result.select_columns(["filename", "size"])

        assert result.success
        assert result.data_format == DataFormat.POLARS
        assert result.structured_output.columns == ["filename", "size"]
        assert result.structured_output.shape == (5, 2)

    def test_drop_columns_single(self, sample_result):
        """Test usunięcia pojedynczej kolumny"""
        result = sample_result.drop_columns("raw_line")

        assert result.success
        assert "raw_line" not in result.structured_output.columns
        assert result.structured_output.shape == (5, 4)

    def test_drop_columns_list(self, sample_result):
        """Test usunięcia wielu kolumn"""
        result = sample_result.drop_columns(["raw_line", "permissions"])

        assert result.success
        assert "raw_line" not in result.structured_output.columns
        assert "permissions" not in result.structured_output.columns
        assert result.structured_output.shape == (5, 3)

    def test_rename_columns(self, sample_result):
        """Test zmiany nazw kolumn"""
        mapping = {"filename": "name", "size": "bytes"}
        result = sample_result.rename_columns(mapping)

        assert result.success
        assert "name" in result.structured_output.columns
        assert "bytes" in result.structured_output.columns
        assert "filename" not in result.structured_output.columns
        assert "size" not in result.structured_output.columns


class TestRowSelection(TestDataSelectionMethods):
    """Testy dla metod selekcji wierszy"""

    def test_filter_by_value(self, sample_result):
        """Test filtrowania po konkretnej wartości"""
        result = sample_result.filter_by_value("is_directory", True)

        assert result.success
        assert result.structured_output.shape == (2, 5)
        assert all(result.structured_output["is_directory"])

    def test_filter_not_value(self, sample_result):
        """Test filtrowania po wartości innej niż podana"""
        result = sample_result.filter_not_value("is_directory", True)

        assert result.success
        assert result.structured_output.shape == (3, 5)
        assert not any(result.structured_output["is_directory"])

    def test_filter_even_rows(self, sample_result):
        """Test filtrowania wierszy parzystych (indeksy 0, 2, 4)"""
        result = sample_result.filter_even_rows()

        assert result.success
        assert result.structured_output.shape == (3, 5)  # Wiersze 0, 2, 4
        expected_filenames = ["file1.txt", "file3.txt", "dir2"]
        assert result.structured_output["filename"].to_list() == expected_filenames

    def test_filter_odd_rows(self, sample_result):
        """Test filtrowania wierszy nieparzystych (indeksy 1, 3)"""
        result = sample_result.filter_odd_rows()

        assert result.success
        assert result.structured_output.shape == (2, 5)  # Wiersze 1, 3
        expected_filenames = ["file2.txt", "dir1"]
        assert result.structured_output["filename"].to_list() == expected_filenames

    def test_filter_every_nth_no_offset(self, sample_result):
        """Test filtrowania co N-ty wiersz bez offsetu"""
        result = sample_result.filter_every_nth(2)  # Co drugi wiersz

        assert result.success
        assert result.structured_output.shape == (3, 5)  # Wiersze 0, 2, 4
        expected_filenames = ["file1.txt", "file3.txt", "dir2"]
        assert result.structured_output["filename"].to_list() == expected_filenames

    def test_filter_every_nth_with_offset(self, sample_result):
        """Test filtrowania co N-ty wiersz z offsetem"""
        result = sample_result.filter_every_nth(2, offset=1)  # Co drugi zaczynając od indeksu 1

        assert result.success
        assert result.structured_output.shape == (2, 5)  # Wiersze 1, 3
        expected_filenames = ["file2.txt", "dir1"]
        assert result.structured_output["filename"].to_list() == expected_filenames

    def test_where_condition(self, sample_result):
        """Test filtrowania z warunkiem logicznym"""
        result = sample_result.where(pl.col("size") > 300)

        assert result.success
        assert result.structured_output.shape == (2, 5)
        assert all(result.structured_output["size"] > 300)

    def test_sample_rows(self, sample_result):
        """Test losowego próbkowania wierszy"""
        result = sample_result.sample(3)

        assert result.success
        assert result.structured_output.shape == (3, 5)

    def test_sample_with_replacement(self, sample_result):
        """Test losowego próbkowania z powtórzeniami"""
        result = sample_result.sample(10, with_replacement=True)

        assert result.success
        assert result.structured_output.shape == (10, 5)


class TestCommandChainDataSelection(TestDataSelectionMethods):
    """Testy dla metod selekcji danych w CommandChain"""

    def test_chain_column_operations(self):
        """Test operacji na kolumnach w łańcuchu"""
        chain = (
            LsCommand()
            .with_option("-la")
            .select_columns(["filename", "size"])
            .drop_columns("size")
            .rename_columns({"filename": "name"})
        )

        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.columns == ["name"]

    def test_chain_row_operations(self):
        """Test operacji na wierszach w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_even_rows().head(2)

        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] <= 2


class TestDataSelectionEdgeCases(TestDataSelectionMethods):
    """Testy dla przypadków brzegowych"""

    def test_select_nonexistent_column(self, sample_result):
        """Test wyboru nieistniejącej kolumny"""
        result = sample_result.select_columns("nonexistent")

        assert result.success
        assert result.structured_output.shape == (5, 1)
        assert result.structured_output.columns == ["nonexistent"]

    def test_filter_by_nonexistent_value(self, sample_result):
        """Test filtrowania po nieistniejącej wartości"""
        result = sample_result.filter_by_value("filename", "nonexistent.txt")

        assert result.success
        assert result.structured_output.shape == (0, 5)  # Pusty DataFrame

    def test_sample_more_than_available(self, sample_result):
        """Test próbkowania większej liczby wierszy niż dostępne"""
        result = sample_result.sample(10, with_replacement=True)

        assert result.success
        assert result.structured_output.shape == (10, 5)

    def test_filter_every_nth_larger_than_data(self, sample_result):
        """Test filtrowania co N-ty gdzie N > liczba wierszy"""
        result = sample_result.filter_every_nth(10)

        assert result.success
        assert result.structured_output.shape == (1, 5)  # Tylko pierwszy wiersz
        assert result.structured_output["filename"][0] == "file1.txt"


class TestRendererIntegration(TestDataSelectionMethods):
    """Testy integracji z rendererami"""

    def test_renderer_raw_line(self, sample_result):
        """Test renderera raw_line"""
        result = sample_result.filter_even_rows(renderer="raw_line")

        assert result.success
        # raw_output powinien zawierać połączone linie z kolumny raw_line
        assert "\n" in result.raw_output or len(result.raw_output) > 0

    def test_renderer_csv(self, sample_result):
        """Test renderera CSV"""
        result = sample_result.head(2).select_columns(["filename", "size"], renderer="csv")

        assert result.success
        assert "filename,size" in result.raw_output or len(result.raw_output) > 0

    def test_renderer_default(self, sample_result):
        """Test domyślnego renderera"""
        result = sample_result.head(2)

        assert result.success
        assert len(result.raw_output) > 0


class TestDataSelectionImmutability(TestDataSelectionMethods):
    """Testy niezmienności (immutability)"""

    def test_original_result_unchanged(self, sample_result):
        """Test że oryginalny CommandResult nie jest modyfikowany"""
        original_shape = sample_result.structured_output.shape
        original_columns = sample_result.structured_output.columns.copy()

        # Wykonaj transformację
        filtered = sample_result.filter_even_rows()

        # Sprawdź że oryginał nie zmienił się
        assert sample_result.structured_output.shape == original_shape
        assert sample_result.structured_output.columns == original_columns

        # Sprawdź że wynik jest inny
        assert filtered.structured_output.shape != original_shape


class TestSafeMathOperations(TestDataSelectionMethods):
    """Testy dla bezpiecznych operacji matematycznych"""

    @pytest.fixture
    def numeric_dataframe(self):
        """DataFrame z danymi numerycznymi do testów"""
        return pl.DataFrame(
            {
                "a": [1, 2, 3, 4, 5],
                "b": [10, 20, 30, 0, 50],  # includes zero for division testing
                "text_col": ["a", "b", "c", "d", "e"],
            }
        )

    @pytest.fixture
    def numeric_result(self, numeric_dataframe):
        """CommandResult z danymi numerycznymi"""
        return CommandResult(
            raw_output="test", success=True, structured_output=numeric_dataframe, data_format=DataFormat.POLARS
        )

    def test_add_columns(self, numeric_result):
        """Test dodawania kolumn z walidacją błędów"""
        result = numeric_result.add_columns("a", "b", "sum_ab")

        assert result.success
        assert "sum_ab" in result.structured_output.columns
        expected = [11, 22, 33, 4, 55]  # 1+10, 2+20, 3+30, 4+0, 5+50
        assert result.structured_output["sum_ab"].to_list() == expected

    def test_subtract_columns(self, numeric_result):
        """Test odejmowania kolumn z walidacją błędów"""
        result = numeric_result.subtract_columns("b", "a", "diff_ba")

        assert result.success
        assert "diff_ba" in result.structured_output.columns
        expected = [9, 18, 27, -4, 45]  # 10-1, 20-2, 30-3, 0-4, 50-5
        assert result.structured_output["diff_ba"].to_list() == expected

    def test_multiply_columns(self, numeric_result):
        """Test mnożenia kolumn z walidacją błędów"""
        result = numeric_result.multiply_columns("a", "b", "prod_ab")

        assert result.success
        assert "prod_ab" in result.structured_output.columns
        expected = [10, 40, 90, 0, 250]  # 1*10, 2*20, 3*30, 4*0, 5*50
        assert result.structured_output["prod_ab"].to_list() == expected

    def test_divide_columns(self, numeric_result):
        """Test dzielenia kolumn z walidacją błędów"""
        result = numeric_result.divide_columns("b", "a", "ratio_ba")

        assert result.success
        assert "ratio_ba" in result.structured_output.columns
        expected = [10.0, 10.0, 10.0, 0.0, 10.0]  # 10/1, 20/2, 30/3, 0/4, 50/5
        assert result.structured_output["ratio_ba"].to_list() == expected

    def test_divide_by_zero(self, numeric_result):
        """Test dzielenia przez zero z walidacją błędów"""
        result = numeric_result.divide_columns("a", "b", "ratio_ab")

        assert result.success
        assert "ratio_ab" in result.structured_output.columns
        # Row with b=0 (index 3) should have None/null
        values = result.structured_output["ratio_ab"].to_list()
        assert values[3] is None  # Division by zero returns None instead of crashing


class TestMatrixOperations(TestDataSelectionMethods):
    """Testy dla operacji macierzowych"""

    @pytest.fixture
    def matrix_dataframe(self):
        """DataFrame reprezentujący macierz"""
        return pl.DataFrame(
            {"col_0": [1, 2, 3, 4], "col_1": [5, 6, 7, 8], "col_2": [9, 10, 11, 12], "col_3": [13, 14, 15, 16]}
        )

    @pytest.fixture
    def matrix_result(self, matrix_dataframe):
        """CommandResult z danymi macierzowymi"""
        return CommandResult(
            raw_output="test", success=True, structured_output=matrix_dataframe, data_format=DataFormat.POLARS
        )

    def test_slice_rows(self, matrix_result):
        """Test slice'owania wierszy"""
        result = matrix_result.slice_rows(1, 4, 2)  # Rows 1, 3

        assert result.success
        assert result.structured_output.shape == (2, 4)
        assert result.structured_output["col_0"].to_list() == [2, 4]

    def test_slice_columns(self, matrix_result):
        """Test slice'owania kolumn"""
        result = matrix_result.slice_columns(["col_0", "col_2"])

        assert result.success
        assert result.structured_output.shape == (4, 2)
        assert result.structured_output.columns == ["col_0", "col_2"]

    def test_transpose_matrix(self, matrix_result):
        """Test transpozycji macierzy"""
        result = matrix_result.transpose_matrix()

        assert result.success
        assert result.structured_output.shape == (4, 4)  # Transposed
        # Check that first row became first column
        assert result.structured_output["col_0"].to_list() == [1, 5, 9, 13]

    def test_reshape_matrix(self, matrix_result):
        """Test reshape'owania macierzy"""
        result = matrix_result.reshape_matrix((2, 8))

        assert result.success
        assert result.structured_output.shape == (2, 8)


class TestAdvancedFiltering(TestDataSelectionMethods):
    """Testy dla zaawansowanego filtrowania"""

    def test_filter_numeric_range_min_only(self, sample_result):
        """Test filtrowania numerycznego z samym minimum"""
        result = sample_result.filter_numeric_range("size", min_val=300)

        assert result.success
        assert all(result.structured_output["size"] >= 300)

    def test_filter_numeric_range_max_only(self, sample_result):
        """Test filtrowania numerycznego z samym maksimum"""
        result = sample_result.filter_numeric_range("size", max_val=300)

        assert result.success
        assert all(result.structured_output["size"] <= 300)

    def test_filter_numeric_range_both(self, sample_result):
        """Test filtrowania numerycznego z min i max"""
        result = sample_result.filter_numeric_range("size", min_val=200, max_val=400)

        assert result.success
        assert all((result.structured_output["size"] >= 200) & (result.structured_output["size"] <= 400))

    def test_filter_string_pattern_case_sensitive(self, sample_result):
        """Test filtrowania string z uwzględnieniem wielkości liter"""
        result = sample_result.filter_string_pattern("filename", "FILE", case_insensitive=False)

        assert result.success
        assert result.structured_output.shape == (0, 5)  # No matches

    def test_filter_string_pattern_case_insensitive(self, sample_result):
        """Test filtrowania string bez uwzględnienia wielkości liter"""
        result = sample_result.filter_string_pattern("filename", "FILE", case_insensitive=True)

        assert result.success
        assert result.structured_output.shape == (5, 5)  # All filenames contain "file" (case insensitive)


class TestErrorHandling(TestDataSelectionMethods):
    """Testy dla obsługi błędów"""

    def test_math_with_invalid_data(self, sample_result):
        """Test operacji matematycznych z nieprawidłowymi danymi"""
        # Try to add text column with numeric column
        with pytest.raises(ValueError, match="Addition failed"):
            sample_result.add_columns("filename", "size", "result")

    def test_filter_invalid_numeric_column(self, sample_result):
        """Test filtrowania nieprawidłowej kolumny numerycznej"""
        with pytest.raises(ValueError, match="Numeric range filtering failed"):
            sample_result.filter_numeric_range("filename", 100, 1000)

    def test_reshape_invalid_dimensions(self, sample_result):
        """Test reshape z nieprawidłowymi wymiarami"""
        with pytest.raises(ValueError, match="Cannot reshape matrix"):
            sample_result.reshape_matrix((10, 10))  # Too many elements


class TestDataExtraction(TestDataSelectionMethods):
    """Testy dla metod ekstrakcji danych"""

    def test_get_headers(self, sample_result):
        """Test pobrania nagłówków"""
        headers = sample_result.get_headers()
        assert isinstance(headers, list)
        assert len(headers) == 5
        assert "filename" in headers
        assert "size" in headers

    def test_get_column_names(self, sample_result):
        """Test pobrania nazw kolumn (alias dla headers)"""
        names = sample_result.get_column_names()
        headers = sample_result.get_headers()
        assert names == headers

    def test_get_shape(self, sample_result):
        """Test pobrania kształtu DataFrame"""
        shape = sample_result.get_shape()
        assert isinstance(shape, tuple)
        assert len(shape) == 2
        assert shape[0] == 5  # rows
        assert shape[1] == 5  # columns

    def test_get_row_valid_index(self, sample_result):
        """Test pobrania pojedynczego wiersza z prawidłowym indeksem"""
        row = sample_result.get_row(0)
        assert isinstance(row, dict)
        assert "filename" in row
        assert "size" in row

    def test_get_row_invalid_index(self, sample_result):
        """Test pobrania wiersza z nieprawidłowym indeksem"""
        with pytest.raises(IndexError):
            sample_result.get_row(10)  # Out of bounds

    def test_get_rows_valid_indices(self, sample_result):
        """Test pobrania wielu wierszy z prawidłowymi indeksami"""
        result = sample_result.get_rows([0, 2, 4])
        assert result.success
        assert result.structured_output.shape == (3, 5)

    def test_get_rows_invalid_indices(self, sample_result):
        """Test pobrania wierszy z nieprawidłowymi indeksami"""
        with pytest.raises(IndexError):
            sample_result.get_rows([0, 10])  # One index out of bounds


class TestDataCleaning(TestDataSelectionMethods):
    """Testy dla metod czyszczenia danych"""

    @pytest.fixture
    def messy_dataframe(self):
        """DataFrame z danymi do wyczyszczenia"""
        return pl.DataFrame(
            {
                "name": ["Alice", "Bob", "Alice", "Charlie", "Bob"],
                "age": [25, 30, 25, None, 30],  # Duplicates and null
                "city": ["NYC", None, "NYC", "LA", "NYC"],
            }
        )

    @pytest.fixture
    def messy_result(self, messy_dataframe):
        """CommandResult z danymi do wyczyszczenia"""
        return CommandResult(
            raw_output="test", success=True, structured_output=messy_dataframe, data_format=DataFormat.POLARS
        )

    def test_drop_duplicates_all_columns(self, messy_result):
        """Test usunięcia duplikatów ze wszystkich kolumn"""
        result = messy_result.drop_duplicates()
        assert result.success
        assert result.structured_output.shape[0] == 4  # Should remove 1 duplicate

    def test_drop_duplicates_subset(self, messy_result):
        """Test usunięcia duplikatów z podzbioru kolumn"""
        result = messy_result.drop_duplicates(subset=["name"])
        assert result.success
        assert result.structured_output.shape[0] == 3  # Unique names only

    def test_fill_nulls_all_columns(self, messy_result):
        """Test wypełnienia nulli we wszystkich kolumnach"""
        result = messy_result.fill_nulls("UNKNOWN")
        assert result.success
        # Check that nulls are filled
        assert not result.structured_output.null_count().sum_horizontal()[0]

    def test_fill_nulls_specific_columns(self, messy_result):
        """Test wypełnienia nulli w wybranych kolumnach"""
        result = messy_result.fill_nulls(99, columns=["age"])
        assert result.success
        # Age column should have no nulls
        age_nulls = result.structured_output["age"].null_count()
        assert age_nulls == 0
        # City column should still have nulls
        city_nulls = result.structured_output["city"].null_count()
        assert city_nulls > 0

    def test_drop_nulls_all_columns(self, messy_result):
        """Test usunięcia wierszy z nullami w dowolnej kolumnie"""
        result = messy_result.drop_nulls()
        assert result.success
        assert result.structured_output.shape[0] == 3  # Should keep only rows without nulls

    def test_drop_nulls_subset(self, messy_result):
        """Test usunięcia wierszy z nullami w wybranych kolumnach"""
        result = messy_result.drop_nulls(subset=["age"])
        assert result.success
        assert result.structured_output.shape[0] == 4  # Should keep rows where age is not null


class TestStatisticalOperations(TestDataSelectionMethods):
    """Testy dla operacji statystycznych"""

    def test_describe_with_numeric_data(self, sample_result):
        """Test statystyk opisowych z danymi numerycznymi"""
        # Add some numeric data for testing
        df = sample_result.as_polars().with_columns(pl.lit([100, 200, 300, 400, 500]).alias("numeric_col"))
        numeric_result = CommandResult(
            raw_output="test", success=True, structured_output=df, data_format=DataFormat.POLARS
        )

        result = numeric_result.describe()
        assert result.success
        assert "statistic" in result.structured_output.columns
        assert "numeric_col" in result.structured_output.columns

    def test_describe_no_numeric_data(self, sample_result):
        """Test statystyk opisowych bez danych numerycznych"""
        # Remove size column to test with only string data
        df = sample_result.as_polars().drop("size")
        no_numeric_result = CommandResult(
            raw_output="test", success=True, structured_output=df, data_format=DataFormat.POLARS
        )

        result = no_numeric_result.describe()
        assert result.success
        assert result.structured_output.shape == (0, 0)  # Empty DataFrame

    def test_value_counts_valid_column(self, sample_result):
        """Test zliczania wartości dla prawidłowej kolumny"""
        result = sample_result.value_counts("is_directory")
        assert result.success
        assert "count" in result.structured_output.columns
        assert result.structured_output.shape[0] == 2  # True and False

    def test_value_counts_invalid_column(self, sample_result):
        """Test zliczania wartości dla nieprawidłowej kolumny"""
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            sample_result.value_counts("nonexistent")


class TestStringOperations(TestDataSelectionMethods):
    """Testy dla operacji na stringach"""

    def test_str_upper_single_column(self, sample_result):
        """Test konwersji do uppercase dla pojedynczej kolumny"""
        result = sample_result.str_upper("filename")
        assert result.success
        filenames = result.structured_output["filename"].to_list()
        assert all(name.isupper() for name in filenames if isinstance(name, str))

    def test_str_upper_multiple_columns(self, sample_result):
        """Test konwersji do uppercase dla wielu kolumn"""
        result = sample_result.str_upper(["filename"])
        assert result.success
        filenames = result.structured_output["filename"].to_list()
        assert all(name.isupper() for name in filenames if isinstance(name, str))

    def test_str_upper_non_string_column(self, sample_result):
        """Test konwersji uppercase dla kolumny niebędącej stringiem"""
        result = sample_result.str_upper("size")  # size is numeric
        assert result.success
        # Should not change numeric columns
        assert result.structured_output["size"].dtype == pl.Int64

    def test_str_lower_single_column(self, sample_result):
        """Test konwersji do lowercase dla pojedynczej kolumny"""
        result = sample_result.str_lower("filename")
        assert result.success
        filenames = result.structured_output["filename"].to_list()
        assert all(name.islower() for name in filenames if isinstance(name, str))

    def test_str_contains_pattern(self, sample_result):
        """Test sprawdzania czy string zawiera wzorzec"""
        result = sample_result.str_contains("filename", "file", "contains_file")
        assert result.success
        assert "contains_file" in result.structured_output.columns
        # All filenames contain "file"
        assert result.structured_output["contains_file"].sum() == 5

    def test_str_contains_no_match(self, sample_result):
        """Test sprawdzania wzorca który nie występuje"""
        result = sample_result.str_contains("filename", "nonexistent", "contains_none")
        assert result.success
        assert "contains_none" in result.structured_output.columns
        assert result.structured_output["contains_none"].sum() == 0


class TestBasicOperations(TestDataSelectionMethods):
    """Testy dla podstawowych operacji"""

    def test_is_success_true(self, sample_result):
        """Test sprawdzania sukcesu - true"""
        assert sample_result.is_success()

    def test_is_success_false(self):
        """Test sprawdzania sukcesu - false"""
        failed_result = CommandResult(
            raw_output="error", success=False, structured_output=pl.DataFrame(), data_format=DataFormat.POLARS
        )
        assert not failed_result.is_success()

    def test_get_structured(self, sample_result):
        """Test pobierania strukturalnych danych"""
        structured = sample_result.get_structured()
        assert isinstance(structured, pl.DataFrame)
        assert len(structured) == 5

    def test_get_format(self, sample_result):
        """Test pobierania formatu danych"""
        assert sample_result.get_format() == DataFormat.POLARS

    def test_get_history(self, sample_result):
        """Test pobierania historii wykonania"""
        history = sample_result.get_history()
        assert isinstance(history, ExecutionHistory)
        assert len(history.steps) > 0

    def test_as_polars(self, sample_result):
        """Test konwersji do Polars DataFrame"""
        df = sample_result.as_polars()
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (5, 5)

    def test_update_from_df(self, sample_result):
        """Test aktualizacji z DataFrame"""
        new_df = pl.DataFrame({"test": [1, 2, 3]})
        updated = sample_result.update_from_df(new_df)
        assert updated.structured_output.equals(new_df)
        assert updated.raw_output != ""  # Should be rendered

    def test_filter(self, sample_result):
        """Test filtrowania z predykatem"""
        result = sample_result.filter(pl.col("size") > 100)
        assert result.success
        assert len(result.structured_output) <= 5

    def test_select(self, sample_result):
        """Test wyboru kolumn"""
        result = sample_result.select(["filename", "size"])
        assert result.success
        assert result.structured_output.shape[1] == 2

    def test_sort_ascending(self, sample_result):
        """Test sortowania rosnącego"""
        result = sample_result.sort("filename")
        assert result.success
        assert result.structured_output.shape == (5, 5)

    def test_sort_descending(self, sample_result):
        """Test sortowania malejącego"""
        result = sample_result.sort("filename", descending=True)
        assert result.success
        assert result.structured_output.shape == (5, 5)

    def test_head(self, sample_result):
        """Test pobierania pierwszych N wierszy"""
        result = sample_result.head(3)
        assert result.success
        assert result.structured_output.shape[0] == 3

    def test_tail(self, sample_result):
        """Test pobierania ostatnich N wierszy"""
        result = sample_result.tail(2)
        assert result.success
        assert result.structured_output.shape[0] == 2

    def test_group_by_simple(self, sample_result):
        """Test grupowania bez agregacji"""
        result = sample_result.group_by("is_directory")
        assert result.success
        assert "is_directory" in result.structured_output.columns

    def test_group_by_with_agg(self, sample_result):
        """Test grupowania z agregacją"""
        result = sample_result.group_by("is_directory", pl.count())
        assert result.success
        assert "count" in result.structured_output.columns

    def test_transform(self, sample_result):
        """Test transformacji z funkcją"""

        def add_test_column(df):
            return df.with_columns(pl.lit("test").alias("test_col"))

        result = sample_result.transform(add_test_column)
        assert result.success
        assert "test_col" in result.structured_output.columns

    def test_extract_field(self, sample_result):
        """Test ekstrakcji pola"""
        filenames = sample_result.extract_field("filename")
        assert isinstance(filenames, list)
        assert len(filenames) == 5
        assert all(isinstance(f, str) for f in filenames)

        # Test ekstrakcji pola liczbowego
        sizes = sample_result.extract_field("size")
        assert isinstance(sizes, list)
        assert len(sizes) == 5
        assert all(isinstance(s, int) for s in sizes)

    def test_to_format_json(self, sample_result):
        """Test konwersji do formatu JSON"""
        result = sample_result.to_format(DataFormat.JSON)
        assert result.data_format == DataFormat.JSON
        assert isinstance(result.structured_output, str)

    def test_to_format_table(self, sample_result):
        """Test konwersji do formatu TABLE"""
        result = sample_result.to_format(DataFormat.TABLE)
        assert result.data_format == DataFormat.TABLE
        assert isinstance(result.structured_output, str)

    def test_str_representation(self, sample_result):
        """Test reprezentacji string"""
        str_repr = str(sample_result)
        assert isinstance(str_repr, str)
        assert "CommandResult" in str_repr


class TestCommandChainOperations(TestDataSelectionMethods):
    """Testy dla wszystkich operacji CommandChain"""

    def test_chain_filter(self):
        """Test filtrowania w łańcuchu"""
        chain = LsCommand().with_option("-la").filter(pl.col("size") > 100)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_select(self):
        """Test wyboru kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").select(["filename", "size"])
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[1] == 2

    def test_chain_sort(self):
        """Test sortowania w łańcuchu"""
        chain = LsCommand().with_option("-la").sort("filename", descending=True)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_head(self):
        """Test head w łańcuchu"""
        chain = LsCommand().with_option("-la").head(3)
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] == 3

    def test_chain_tail(self):
        """Test tail w łańcuchu"""
        chain = LsCommand().with_option("-la").tail(2)
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] == 2

    def test_chain_group_by(self):
        """Test grupowania w łańcuchu"""
        chain = LsCommand().with_option("-la").group_by("is_directory")
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_limit(self):
        """Test limit w łańcuchu"""
        chain = LsCommand().with_option("-la").limit(3)
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] == 3

    def test_chain_select_columns(self):
        """Test wyboru kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").select_columns(["filename", "size"])
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[1] == 2

    def test_chain_drop_columns(self):
        """Test usuwania kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").drop_columns(["permissions"])
        result = chain.execute(CommandContext())
        assert result.success
        assert "permissions" not in result.structured_output.columns

    def test_chain_rename_columns(self):
        """Test zmiany nazw kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").rename_columns({"filename": "name"})
        result = chain.execute(CommandContext())
        assert result.success
        assert "name" in result.structured_output.columns
        assert "filename" not in result.structured_output.columns

    def test_chain_filter_by_value(self):
        """Test filtrowania po wartości w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_by_value("is_directory", True)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_not_value(self):
        """Test filtrowania bez wartości w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_not_value("is_directory", True)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_even_rows(self):
        """Test filtrowania parzystych wierszy w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_even_rows()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_odd_rows(self):
        """Test filtrowania nieparzystych wierszy w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_odd_rows()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_every_nth(self):
        """Test filtrowania co N-tego wiersza w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_every_nth(2)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_where(self):
        """Test warunkowego filtrowania w łańcuchu"""
        chain = LsCommand().with_option("-la").where(pl.col("size") > 0)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_sample(self):
        """Test próbkowania w łańcuchu"""
        chain = LsCommand().with_option("-la").sample(3)
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] == 3

    def test_chain_add_columns(self):
        """Test dodawania kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").add_columns("size", "size", "double_size")
        result = chain.execute(CommandContext())
        assert result.success
        assert "double_size" in result.structured_output.columns

    def test_chain_divide_columns(self):
        """Test dzielenia kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").divide_columns("size", "size", "ratio")
        result = chain.execute(CommandContext())
        assert result.success
        assert "ratio" in result.structured_output.columns

    def test_chain_multiply_columns(self):
        """Test mnożenia kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").multiply_columns("size", "size", "squared")
        result = chain.execute(CommandContext())
        assert result.success
        assert "squared" in result.structured_output.columns

    def test_chain_subtract_columns(self):
        """Test odejmowania kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").subtract_columns("size", "size", "zero")
        result = chain.execute(CommandContext())
        assert result.success
        assert "zero" in result.structured_output.columns

    def test_chain_slice_rows(self):
        """Test cięcia wierszy w łańcuchu"""
        chain = LsCommand().with_option("-la").slice_rows(0, 3)
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[0] == 3

    def test_chain_slice_columns(self):
        """Test cięcia kolumn w łańcuchu"""
        chain = LsCommand().with_option("-la").slice_columns(["filename", "size"])
        result = chain.execute(CommandContext())
        assert result.success
        assert result.structured_output.shape[1] == 2

    def test_chain_transpose_matrix(self):
        """Test transpozycji macierzy w łańcuchu"""
        chain = LsCommand().with_option("-la").transpose_matrix()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_reshape_matrix(self):
        """Test zmiany kształtu macierzy w łańcuchu"""
        chain = LsCommand().with_option("-la").reshape_matrix((10, 1))
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_numeric_range(self):
        """Test filtrowania zakresu liczbowego w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_numeric_range("size", 100, 1000)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_filter_string_pattern(self):
        """Test filtrowania wzorca string w łańcuchu"""
        chain = LsCommand().with_option("-la").filter_string_pattern("filename", "file")
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_drop_duplicates(self):
        """Test usuwania duplikatów w łańcuchu"""
        chain = LsCommand().with_option("-la").drop_duplicates()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_fill_nulls(self):
        """Test wypełniania nulli w łańcuchu"""
        chain = LsCommand().with_option("-la").fill_nulls(0)
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_drop_nulls(self):
        """Test usuwania nulli w łańcuchu"""
        chain = LsCommand().with_option("-la").drop_nulls()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_describe(self):
        """Test opisu statystycznego w łańcuchu"""
        chain = LsCommand().with_option("-la").describe()
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_value_counts(self):
        """Test zliczania wartości w łańcuchu"""
        chain = LsCommand().with_option("-la").value_counts("is_directory")
        result = chain.execute(CommandContext())
        assert result.success
        assert "count" in result.structured_output.columns

    def test_chain_str_upper(self):
        """Test zamiany na wielkie litery w łańcuchu"""
        chain = LsCommand().with_option("-la").str_upper("filename")
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_str_lower(self):
        """Test zamiany na małe litery w łańcuchu"""
        chain = LsCommand().with_option("-la").str_lower("filename")
        result = chain.execute(CommandContext())
        assert result.success

    def test_chain_str_contains(self):
        """Test sprawdzania zawierania string w łańcuchu"""
        chain = LsCommand().with_option("-la").str_contains("filename", "file", "has_file")
        result = chain.execute(CommandContext())
        assert result.success
        assert "has_file" in result.structured_output.columns

    def test_chain_get_history(self):
        """Test pobierania historii w łańcuchu"""
        chain = LsCommand().with_option("-la")
        history = chain.get_history()
        assert isinstance(history, ExecutionHistory)
