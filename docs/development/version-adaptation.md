# Command Behavior Adaptation Based on Tool Versions

Mancer allows commands to automatically adapt their behavior based on the detected version of the underlying tool. This is particularly useful for handling changes in command output formats or options across different versions of system tools.

## How Version Adaptation Works

1. **Version Detection**: When a command is executed, it automatically checks the version of the tool it's using.
2. **Method Adaptation**: Based on the detected version, the command can use different parsing methods to handle output.
3. **Backward Compatibility**: This allows your code to work with different tool versions without requiring conditional logic.

## Implementing Version-Specific Behavior

### 1. Define Version Adapters

To create a command with version-specific behavior, define a mapping between version patterns and method names:

```python
class MyVersionedCommand(BaseCommand):
    # Tool name for version checking
    tool_name = "my_tool"
    
    # Version adapters mapping 
    version_adapters = {
        "1.x": "_parse_output_v1",
        "2.x": "_parse_output_v2",
        "3.x": "_parse_output_v3"
    }
```

### 2. Implement Version-Specific Methods

Implement version-specific methods for parsing or other behaviors:

```python
def _parse_output_v1(self, raw_output: str):
    # Parsing logic specific to version 1.x
    # Handle older output format
    lines = raw_output.strip().split('\n')
    result = []
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                result.append({
                    'name': parts[0],
                    'value': parts[1]
                })
    return result

def _parse_output_v2(self, raw_output: str):
    # Enhanced parsing logic for version 2.x
    # Handle newer output format with additional fields
    lines = raw_output.strip().split('\n')
    result = []
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 3:
                result.append({
                    'name': parts[0],
                    'value': parts[1],
                    'description': parts[2]
                })
    return result

def _parse_output_v3(self, raw_output: str):
    # Latest parsing logic for version 3.x
    # Handle newest output format with JSON-like structure
    try:
        import json
        return json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback to v2 parsing if JSON parsing fails
        return self._parse_output_v2(raw_output)
```

### 3. Version Pattern Matching

Mancer supports various version pattern formats:

- **Exact version**: `"3.8"` matches exactly version 3.8
- **Major version**: `"3.x"` matches any 3.x version
- **Version range**: `"3.8-3.10"` matches versions 3.8 through 3.10
- **Minimum version**: `"3.8+"` matches version 3.8 and higher

## Examples of Version Adaptation

### DF Command Example

The `df` command demonstrates version adaptation:

```python
class DfCommand(BaseCommand):
    tool_name = "df"
    
    version_adapters = {
        "2.x": "_parse_output_v2",
        "8.x": "_parse_output_v8", 
        "9.x": "_parse_output_v9"
    }
    
    def _parse_output_v2(self, raw_output: str):
        # Parse older df output format
        # Handle different column layouts
        
    def _parse_output_v8(self, raw_output: str):
        # Parse modern df output format
        # Handle current column layouts
        
    def _parse_output_v9(self, raw_output: str):
        # Parse latest df output format
        # Handle newest features and layouts
```

### PS Command Example

The `ps` command also uses version adaptation:

```python
class PsCommand(BaseCommand):
    tool_name = "ps"
    
    version_adapters = {
        "2.x": "_parse_output_v2",
        "3.x": "_parse_output_v3"
    }
    
    def _parse_output_v2(self, raw_output: str):
        # Parse older ps output format
        # Handle legacy column layouts
        
    def _parse_output_v3(self, raw_output: str):
        # Parse modern ps output format
        # Handle current column layouts
```

## Best Practices for Version Adaptation

### 1. Fallback Strategy

Always provide a fallback parsing method:

```python
def _parse_output(self, raw_output: str):
    # Try version-specific parsing first
    if hasattr(self, '_parse_output_versioned'):
        try:
            return self._parse_output_versioned(raw_output)
        except Exception:
            pass
    
    # Fallback to default parsing
    return self._parse_output_default(raw_output)
```

### 2. Version Detection Logging

Log version detection for debugging:

```python
def execute(self, context: CommandContext, input_result=None) -> CommandResult:
    # Detect tool version
    version = self._detect_tool_version(context)
    
    # Log version for debugging
    if hasattr(self, 'logger'):
        self.logger.debug(f"Using {self.tool_name} version {version}")
    
    # Execute with version-specific behavior
    return self._execute_with_version(version, context, input_result)
```

### 3. Error Handling

Handle parsing errors gracefully:

```python
def _parse_output_versioned(self, raw_output: str):
    try:
        # Try version-specific parsing
        return self._get_version_parser()(raw_output)
    except Exception as e:
        # Log error and fallback
        if hasattr(self, 'logger'):
            self.logger.warning(f"Version-specific parsing failed: {e}")
        return self._parse_output_default(raw_output)
```

### 4. Testing Different Versions

Test your version adapters with different tool versions:

```python
def test_version_adaptation():
    # Test with different versions
    versions = ["2.34", "3.8", "9.0"]
    
    for version in versions:
        command = MyVersionedCommand()
        command._mock_tool_version(version)  # Mock version for testing
        
        # Test parsing with version-specific output
        test_output = generate_test_output_for_version(version)
        result = command._parse_output(test_output)
        
        assert result is not None
        assert len(result) > 0
```

## Configuration and Management

### Tool Version Registry

Manage allowed versions in configuration:

```yaml
# tool_versions.yaml
allowed_versions:
  df:
    - "2.34"
    - "8.0"
    - "9.0"
  ps:
    - "2.34"
    - "3.0"
  grep:
    - "3.7"
    - "3.8"
```

### Version Validation

Validate detected versions against allowed versions:

```python
def _validate_version(self, detected_version: str) -> bool:
    from mancer.domain.model.tool_version import ToolVersionRegistry
    
    registry = ToolVersionRegistry()
    allowed_versions = registry.get_allowed_versions(self.tool_name)
    
    if not allowed_versions:
        return True  # No restrictions
    
    return any(self._version_matches(detected_version, allowed) 
               for allowed in allowed_versions)
```

## Troubleshooting Version Adaptation

### Common Issues

1. **Version Detection Fails**
   - Check if the tool supports `--version` or `-V` flag
   - Verify the tool is in PATH
   - Check for permission issues

2. **Parsing Methods Not Found**
   - Ensure version adapter methods are properly named
   - Check that version patterns match detected versions
   - Verify method signatures match the base class

3. **Fallback Not Working**
   - Implement a robust default parsing method
   - Add error handling and logging
   - Test with various output formats

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Version Detection**
   ```python
   version = command._detect_tool_version(context)
   print(f"Detected version: {version}")
   ```

3. **Test Individual Parsers**
   ```python
   result = command._parse_output_v2(test_output)
   print(f"V2 parser result: {result}")
   ```

## Future Enhancements

### Planned Features

1. **Automatic Version Detection**: Detect tool versions without explicit commands
2. **Version Compatibility Matrix**: Define compatibility between different tool versions
3. **Smart Fallbacks**: Intelligent fallback strategies based on version similarity
4. **Version Migration**: Tools to help migrate between different tool versions

### Contributing Version Adapters

When contributing new version adapters:

1. Test with multiple tool versions
2. Include comprehensive test cases
3. Document version-specific behavior
4. Provide migration examples if needed
