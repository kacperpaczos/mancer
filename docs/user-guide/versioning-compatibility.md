# Versioning & Compatibility

This page explains version information for the Mancer package itself and strategies for dealing with external tool versions used by commands.

## Mancer package version
Use VersionInfo to read the installed Mancer version at runtime.

```python
from mancer.domain.model.version_info import VersionInfo

vi = VersionInfo.get_mancer_version()
print(str(vi))          # e.g., "mancer v0.1.3"
print(vi.version)       # e.g., "0.1.3"
print(vi.summary)
```

Notes:
- If Mancer is not installed via pip (development mode), version may be reported as "dev".
- You can surface this in your apps for diagnostics or support banners.

## External tool versions (system commands)
Some commands rely on system tools (e.g., df, ps, grep). To manage compatibility, Mancer provides models for parsing and tracking tool versions.

### ToolVersion
Represents a detected version of a system tool.

```python
from mancer.domain.model.tool_version import ToolVersion

# Parse "--version" output for a tool
raw = "grep (GNU grep) 3.8\nCopyright (C) ..."
tv = ToolVersion.parse_version_output("grep", raw)
print(tv.name, tv.version)
```

### ToolVersionRegistry
Tracks allowed versions and what was detected at runtime.

```python
from mancer.domain.model.tool_version import ToolVersion, ToolVersionRegistry

registry = ToolVersionRegistry()
# Declare allowed versions (policy)
registry.register_allowed_versions("grep", ["3.7", "3.8"]) 

# Simulate detection
detected = ToolVersion.parse_version_output("grep", "grep (GNU grep) 3.8")
registry.update_detected_version(detected)

# Validate
if not registry.is_version_allowed("grep", detected.version):
    print("Warning: unsupported grep version:", detected.version)
```

### Adapter-based parsing in commands
Concrete command implementations can declare a mapping of supported tool versions to parsing functions, e.g. DfCommand:

- It defines a preferred output format and version adapters:
  - version_adapters = {"2.x": "_parse_output_v2", "8.x": "_parse_output_v8", "9.x": "_parse_output_v9"}
- At runtime, the command selects the best parser based on the detected tool version.

This design allows:
- Backward compatibility with multiple tool versions
- Gradual introduction of new parsers without breaking older environments

## Recommended practices
- Detect and log tool versions at startup in long‑running services (once per tool)
- Gate behavior or parsing paths based on detected versions
- Maintain an explicit compatibility policy for key tools (document allowed versions)
- In CI, run tests across representative tool versions when feasible (e.g., via Docker images)

## Troubleshooting compatibility
- If parsing fails after an OS/tool upgrade:
  - Log raw outputs and detected versions for diagnostics
  - Temporarily fall back to a more permissive parser if available
  - Add/adjust an adapter for the new version and update tests

## Stability notes
- Mancer’s own API is evolving (early version); prefer pinning versions in requirements and testing upgrades in a staging environment.

