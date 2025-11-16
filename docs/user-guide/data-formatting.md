# Data & Formatting

This guide explains how command results are structured and how to work with Polars DataFrames in command chains.

Mancer commands return a CommandResult, which contains:
- raw_output: the original string output (used for bash pipelines)
- structured_output: a Polars DataFrame by default
- data_format: the current format of structured_output (DataFormat)

## Inspecting CommandResult
```python
import polars as pl
from mancer.infrastructure.command.system.df_command import DfCommand
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()
res = DfCommand().with_flag("human-readable").execute(ctx)

print("Success:", res.is_success())
print("Format:", res.get_format())
print("DataFrame shape:", res.get_structured().shape)
print("Schema:", res.get_structured().schema)
print("First 3 rows:", res.get_structured().head(3))
```

## Extracting fields
Extract a column from the Polars DataFrame:
```python
values = res.extract_field("MountedOn")  # Extract column as list
print(values[:5])

# Or work directly with Polars
df = res.as_polars()
mounted_values = df["MountedOn"].to_list()
print(mounted_values[:5])
```

## Available formats (DataFormat)
- POLARS (default) – polars.DataFrame (canonical format)
- JSON – JSON string
- TABLE – tabular representation used by some commands (e.g., df, ps)

```python
from mancer.domain.model.data_format import DataFormat
print(DataFormat.POLARS, DataFormat.JSON, DataFormat.TABLE)
```

## Converting data (to_format)
Use CommandResult.to_format(target_format) to convert between formats.

```python
from mancer.domain.model.data_format import DataFormat

# Convert to JSON
as_json = res.to_format(DataFormat.JSON)
print("JSON sample:", as_json.structured_output[:120])

# Convert to TABLE format
as_table = res.to_format(DataFormat.TABLE)
print("Table format:")
print(as_table.structured_output[:200])
```

## Transforming DataFrames

### Using fluent transformation methods
The easiest way to transform data is using built-in fluent methods:

```python
import polars as pl
from mancer.infrastructure.command.system.ls_command import LsCommand
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()

# Chain with fluent DataFrame transformations
result = (LsCommand().with_option("-la")
          .filter(pl.col("is_directory") == True)  # Filter directories
          .head(3)  # Take first 3
          .select(["filename", "size"])  # Select columns
          .sort("size", descending=True)  # Sort by size
          .execute(ctx))

print("Top 3 largest directories:", result.structured_output)
```

### Advanced selection examples

```python
# Column operations
result = (LsCommand().with_option("-la")
          .select_columns(["filename", "size", "permissions"])  # Select specific columns
          .drop_columns("permissions")  # Remove permissions column
          .rename_columns({"filename": "name", "size": "bytes"})  # Rename columns
          .execute(ctx))

# Row selection by patterns
result = (LsCommand().with_option("-la")
          .filter_even_rows()  # Every other row (0, 2, 4, ...)
          .filter_every_nth(3)  # Every 3rd row
          .filter_by_value("is_directory", True)  # Only directories
          .execute(ctx))

# Conditional and sampling operations
result = (LsCommand().with_option("-la")
          .where(pl.col("size") > 1000)  # Size > 1000 bytes
          .sample(5)  # Random sample of 5 files
          .execute(ctx))
```

Available fluent methods:

**Basic operations:**
- `filter(predicate)` - Filter rows by condition
- `select(columns)` - Select columns by name(s)
- `sort(by, descending=False)` - Sort rows
- `head(n=5)` / `tail(n=5)` / `limit(n)` - Take first/last N rows
- `group_by(by, agg=None)` - Group and optionally aggregate

**Data inspection:**
- `get_headers()` / `get_column_names()` - Get column names
- `get_shape()` - Get DataFrame dimensions (rows, columns)
- `get_row(index)` - Get single row by index as dict
- `get_rows(indices)` - Get multiple rows by indices

**Data cleaning:**
- `drop_duplicates(subset=None)` - Remove duplicate rows
- `fill_nulls(value, columns=None)` - Fill null values
- `drop_nulls(subset=None)` - Remove rows with nulls

**Statistics and analysis:**
- `describe(percentiles=None)` - Generate descriptive statistics
- `value_counts(column, sort=True)` - Count unique values in column

**String operations:**
- `str_upper(columns)` - Convert to uppercase
- `str_lower(columns)` - Convert to lowercase
- `str_contains(column, pattern, new_column)` - Check if contains pattern

**Advanced column operations:**
- `select_columns(columns)` - Select columns (string or list)
- `drop_columns(columns)` - Drop columns (string or list)
- `rename_columns(mapping)` - Rename columns using dict mapping

**Advanced row operations:**
- `filter_by_value(column, value)` - Filter rows where column equals value
- `filter_not_value(column, value)` - Filter rows where column does NOT equal value
- `filter_even_rows()` - Select even-indexed rows (0, 2, 4, ...)
- `filter_odd_rows()` - Select odd-indexed rows (1, 3, 5, ...)
- `filter_every_nth(n, offset=0)` - Select every Nth row starting from offset
- `where(condition)` - Filter using boolean expression
- `sample(n, with_replacement=False)` - Random sampling

### Using map_df for custom transformations
For complex transformations, use `map_df()` with custom functions:

```python
# Custom transformation with map_df
result = (LsCommand().with_option("-la")
          .map_df(lambda df: df.filter(pl.col("size") > 1000))
          .map_df(lambda df: df.with_columns(
              file_size_mb = pl.col("size") / (1024*1024)
          ))
          .execute(ctx))
```

### Working directly with CommandResult
You can also transform CommandResult after execution:

```python
result = LsCommand().execute(ctx)
filtered = result.filter(pl.col("is_directory") == True).head(5)
print("Filtered result:", filtered.structured_output)
```

All transformation methods:
- Return new CommandResult/CommandChain instances (immutable)
- Automatically update `raw_output` for bash pipeline compatibility
- Support custom renderers for text output formatting

## Advanced Filtering Language

Mancer provides a comprehensive filtering language with safe mathematical operations and error validation.

### Safe Mathematical Operations

All mathematical operations automatically handle type conversion and validation:

```python
import polars as pl
from mancer.infrastructure.command.system.ls_command import LsCommand
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()

# Safe mathematical operations with error handling
result = (LsCommand().with_option("-la")
          .add_columns("size", "size", "double_size")  # size + size
          .divide_columns("double_size", "size", "ratio")  # double_size / size (safe division)
          .filter(pl.col("ratio") == 2.0)  # Should always be 2.0
          .execute(ctx))
```

Available mathematical operations:
- `add_columns(col1, col2, new_col)` - Add two columns with error validation
- `subtract_columns(col1, col2, new_col)` - Subtract two columns with error validation
- `multiply_columns(col1, col2, new_col)` - Multiply two columns with error validation
- `divide_columns(col1, col2, new_col)` - Divide two columns with error validation (handles division by zero)

### Matrix Operations

Work with data as matrices/arrays:

```python
# Matrix operations
result = (LsCommand().with_option("-la")
          .slice_rows(0, 10, 2)  # Every other row: 0, 2, 4, 6, 8
          .slice_columns(["filename", "size"])  # Select specific columns
          .transpose_matrix()  # Transpose the matrix
          .execute(ctx))
```

Matrix operations:
- `slice_rows(start, end, step)` - Slice rows like array[start:end:step]
- `slice_columns(column_list)` - Select specific columns
- `transpose_matrix()` - Transpose DataFrame
- `reshape_matrix(new_shape)` - Reshape to new dimensions

### Advanced Filtering Functions

Pre-built filtering functions with validation:

```python
from mancer.domain.service.filtering import range_filter, pattern_filter, safe_add

# Numeric range filtering
result = (LsCommand().with_option("-la")
          .filter_numeric_range("size", min_val=1000, max_val=10000)
          .execute(ctx))

# String pattern matching
result = (LsCommand().with_option("-la")
          .filter_string_pattern("filename", r"\.py$", case_insensitive=True)
          .execute(ctx))

# Using filtering language functions
result = (LsCommand().with_option("-la")
          .transform(safe_add("size", "size", "double_size"))
          .filter(pl.col("double_size") > 2000)
          .execute(ctx))
```

### Error Handling

All filtering operations include comprehensive error validation:

```python
# This will raise FilteringError if columns contain non-numeric data
try:
    result = command.add_columns("text_column", "size", "result").execute(ctx)
except FilteringError as e:
    print(f"Operation failed: {e}")

# Safe division returns None for division by zero instead of crashing
result = command.divide_columns("size", "zero_column", "ratio").execute(ctx)
# ratio will be None where zero_column == 0
```

### Data Inspection and Row Extraction

Extract specific rows or inspect DataFrame structure:

```python
# Get DataFrame information
result = LsCommand().execute(ctx)
print("Shape:", result.get_shape())          # (rows, columns)
print("Headers:", result.get_headers())      # ['filename', 'size', ...]

# Extract specific rows
first_row = result.get_row(0)                # First row as dict
first_three = result.get_rows([0, 1, 2])     # First three rows as DataFrame
```

### Data Cleaning Operations

Handle duplicates and missing values:

```python
# Remove duplicates
cleaned = result.drop_duplicates()

# Fill null values
filled = result.fill_nulls(0)                 # Fill all nulls with 0
filled_cols = result.fill_nulls("N/A", ["column1", "column2"])  # Fill specific columns

# Remove rows with nulls
no_nulls = result.drop_nulls()
no_nulls_cols = result.drop_nulls(["important_col"])  # Check specific columns
```

### Statistical Analysis

Generate statistics and value counts:

```python
# Descriptive statistics
stats = result.describe()                     # Mean, std, min, max, percentiles

# Value counts for categorical columns
counts = result.value_counts("filename")      # Count occurrences of each filename
```

### String Operations

Manipulate text data:

```python
# Case conversion
upper = result.str_upper("filename")          # Convert filename to uppercase
lower = result.str_lower(["filename", "path"]) # Convert multiple columns

# Pattern matching
pattern_match = result.str_contains("filename", ".txt", "is_text_file")  # Add boolean column
```

### Custom Filter Expressions

For advanced users, create custom filter expressions with safety validation:

```python
from mancer.domain.service.filtering import FilterLanguage

# Custom filter with safe evaluation
custom_filter = FilterLanguage.custom_filter("pl.col('size') > 1000 & pl.col('filename').str.contains('.txt')")

result = (LsCommand().with_option("-la")
          .transform(custom_filter)
          .execute(ctx))
```

## Pandas/Polars vs Mancer API

Mancer provides the most commonly used pandas/polars operations with a consistent, safe API:

### ✅ **Implemented Core Operations:**
- **Data Selection**: `select_columns()`, `get_row()`, `get_rows()`, `sample()`
- **Filtering**: `filter()`, `where()`, `filter_by_value()`, `filter_string_pattern()`
- **Sorting**: `sort()`, `head()`, `tail()`
- **Aggregation**: `group_by()`, `describe()`, `value_counts()`
- **Data Cleaning**: `drop_duplicates()`, `fill_nulls()`, `drop_nulls()`
- **String Ops**: `str_upper()`, `str_lower()`, `str_contains()`
- **Math Ops**: `add_columns()`, `divide_columns()`, etc.
- **Matrix Ops**: `slice_rows()`, `slice_columns()`, `transpose_matrix()`

### 🚧 **Not Yet Implemented (could be added):**
- **Joins/Merges**: `merge()`, `join()`
- **Pivot Operations**: `pivot()`, `melt()`
- **Rolling Windows**: `rolling_mean()`, `rolling_sum()`
- **Date Operations**: `dt.year`, `dt.month`, etc.
- **Advanced I/O**: `to_csv()`, `to_json()`, `to_parquet()`
- **Index Operations**: `reset_index()`, `set_index()`
- **Resampling**: Time series resampling
- **Advanced Stats**: `corr()`, `cov()`, hypothesis testing

### 💡 **Mancer Advantages:**
- **Safe Operations**: All math operations validate types and handle errors
- **Immutable**: All methods return new objects (no side effects)
- **Consistent API**: Same methods on `CommandResult` and `CommandChain`
- **Bash Integration**: Automatic `raw_output` updates for shell compatibility
- **Fluent Interface**: Chain operations naturally
- **Error Handling**: Meaningful error messages instead of crashes

All operations are designed to be safe, predictable, and composable for command-line data processing workflows.

### Available Filter Functions

**Convenience functions:**
- `range_filter(column, min_val, max_val)` - Numeric range filter
- `pattern_filter(column, pattern, case_insensitive=True)` - Regex pattern filter
- `safe_add(col1, col2, new_col)` - Safe addition operation
- `safe_subtract(col1, col2, new_col)` - Safe subtraction operation
- `safe_multiply(col1, col2, new_col)` - Safe multiplication operation
- `safe_divide(col1, col2, new_col)` - Safe division operation
- `matrix_slice(rows, cols)` - Matrix slicing operation

**Error handling:**
- All functions validate input types and raise `FilteringError` for invalid operations
- Mathematical operations convert strings to numbers safely
- Division by zero returns `None` instead of crashing
- Invalid data types are properly handled with meaningful error messages

## Choosing preferred format in chains
Command chains can carry a preferred data format for the last command:
```python
from mancer.domain.service.command_chain_service import CommandChain
from mancer.infrastructure.command.system.ps_command import PsCommand
from mancer.infrastructure.command.system.grep_command import GrepCommand
from mancer.domain.model.data_format import DataFormat
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()
chain = PsCommand().with_option("-ef").pipe(GrepCommand("python"))
# Request TABLE format for the last command
chain = chain.with_data_format(DataFormat.TABLE)
res = chain.execute(ctx)
print("Result format:", res.data_format)
```

## Notes
- Conversions pass through an intermediate POLARS DataFrame representation under the hood (DataFormatConverter).
- If a conversion is not possible, to_format returns a failure result (success=False).
- All commands use POLARS format by default, ensuring consistent DataFrame-based processing.
- The `raw_output` field is automatically updated after DataFrame transformations to maintain compatibility with bash pipelines.

