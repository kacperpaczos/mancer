# Data & Formatting

This guide explains how command results are structured and how to convert between data formats.

Mancer commands return a CommandResult, which contains:
- raw_output: the original string output
- structured_output: a list of records (list of dicts/objects) by default
- data_format: the current format of structured_output (DataFormat)

## Inspecting CommandResult
```python
from mancer.infrastructure.command.system.df_command import DfCommand
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()
res = DfCommand().with_flag("human-readable").execute(ctx)

print("Success:", res.is_success())
print("Format:", res.get_format())
print("First record:", res.get_structured()[0] if res.get_structured() else None)
```

## Extracting fields
If structured_output is a list of dicts, you can quickly extract a column:
```python
values = res.extract_field("MountedOn")  # or any key present in the records
print(values[:5])
```

## Available formats (DataFormat)
- LIST (default) – list of dicts/objects
- TABLE – tabular representation used by some commands (e.g., df, ps)
- JSON – JSON string
- DATAFRAME – pandas.DataFrame (requires pandas)
- NDARRAY – numpy.ndarray (requires numpy)

```python
from mancer.domain.model.data_format import DataFormat
print(DataFormat.LIST, DataFormat.TABLE, DataFormat.JSON, DataFormat.DATAFRAME, DataFormat.NDARRAY)
```

## Converting data (to_format)
Use CommandResult.to_format(target_format) to convert. Conversions to DATAFRAME/NDARRAY require optional dependencies.

```python
from mancer.domain.model.data_format import DataFormat

# Convert to JSON
as_json = res.to_format(DataFormat.JSON)
print("JSON sample:", as_json.structured_output[:120])

# Convert to pandas DataFrame
try:
    as_df = res.to_format(DataFormat.DATAFRAME)
    print("DataFrame shape:", as_df.structured_output.shape)
except Exception:
    print("pandas not installed – install it to use DATAFRAME format")

# Convert to NumPy array
try:
    as_np = res.to_format(DataFormat.NDARRAY)
    print("ndarray shape:", as_np.structured_output.shape)
except Exception:
    print("numpy not installed – install it to use NDARRAY format")
```

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
- Conversions pass through an intermediate LIST representation under the hood (DataFormatConverter).
- If a conversion is not possible or an optional dependency is missing, to_format returns a failure result (success=False).
- Some commands set a non-default preferred_data_format, and BaseCommand will convert automatically to it (see df/ps implementations).

