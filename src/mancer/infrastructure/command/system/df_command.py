import re
from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class DfCommand(BaseCommand):
    """Command implementation for the 'df' command to show disk space usage"""

    # Define tool name
    tool_name = "df"

    # Version adapters mapping
    version_adapters = {
        "2.x": "_parse_output_v2",
        "8.x": "_parse_output_v8",
        "9.x": "_parse_output_v9",
    }

    def __init__(self):
        super().__init__("df")
        self.preferred_data_format = DataFormat.TABLE

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """Executes the df command"""
        # Call base method to check tool version
        super().execute(context, input_result)

        # Build the command string
        command_str = self.build_command()

        # Get the appropriate backend
        backend = self._get_backend(context)

        # Execute the command
        exit_code, output, error = backend.execute(command_str)

        # Check if command was successful
        success = exit_code == 0
        error_message = error if error and not success else None

        # Add version warnings to metadata
        metadata = {}
        warnings = context.get_parameter("warnings", [])
        if warnings:
            metadata["version_warnings"] = warnings

        # Create and return the result
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
        )

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Default parser for df command output"""
        lines = raw_output.strip().split("\n")

        if len(lines) < 2:
            return []

        # Get headers from the first line
        headers = re.findall(r"[\w%-]+", lines[0])
        results = []

        for line in lines[1:]:
            if not line.strip():
                continue

            # Split the line into parts
            parts = line.split()

            # Handle filesystem with spaces in name (merge back together)
            if len(parts) > len(headers):
                excess = len(parts) - len(headers) + 1
                filesystem = " ".join(parts[:excess])
                parts = [filesystem] + parts[excess:]

            # Create a dictionary with header keys and values
            entry = {}
            for i, header in enumerate(headers):
                if i < len(parts):
                    # Clean up header names
                    clean_header = header.lower().replace("-", "_").replace("%", "percent")

                    # Try to convert numeric values
                    value = parts[i]
                    if clean_header not in [
                        "filesystem",
                        "mounted",
                        "on",
                        "mount_point",
                    ]:
                        try:
                            # Remove % sign if present
                            if value.endswith("%"):
                                value = value[:-1]

                            # Convert to number if possible
                            if "." in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass  # Keep as string if conversion fails

                    entry[clean_header] = value

            # Handle "Mounted on" special case which often appears as two separate headers
            if "on" in entry and "mounted" in entry:
                entry["mount_point"] = entry["on"]
                del entry["on"]
                del entry["mounted"]

            results.append(entry)

        return results

    def _parse_output_v2(self, raw_output: str) -> List[Dict[str, Any]]:
        """
        Parser specific to df version 2.x (e.g., util-linux df)
        The output format is different from the GNU coreutils version
        """
        lines = raw_output.strip().split("\n")

        if len(lines) < 2:
            return []

        results = []

        # Version 2.x typically has a simpler format with fixed headers
        # Filesystem, Size, Used, Avail, Use%, Mounted on
        for line in lines[1:]:
            if not line.strip():
                continue

            parts = line.split()

            # Ensure we have at least 6 parts
            if len(parts) < 6:
                continue

            # Create a dictionary with standard keys
            entry = {
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "use_percent": parts[4].rstrip("%"),  # Remove % sign
                "mount_point": parts[5] if len(parts) >= 6 else "unknown",
            }

            # Add a version marker
            entry["parser_version"] = "2.x"

            results.append(entry)

        return results

    def _parse_output_v8(self, raw_output: str) -> List[Dict[str, Any]]:
        """
        Parser specific to df version 8.x (GNU coreutils)
        """
        lines = raw_output.strip().split("\n")

        if len(lines) < 2:
            return []

        # Get headers from the first line for flexibility
        headers = re.findall(r"[\w%-]+", lines[0])
        results = []

        for line in lines[1:]:
            if not line.strip():
                continue

            # Split the line into parts
            parts = line.split()

            # Handle filesystem with spaces in name
            if len(parts) > len(headers):
                excess = len(parts) - len(headers) + 1
                filesystem = " ".join(parts[:excess])
                parts = [filesystem] + parts[excess:]

            # Create a dictionary with header keys and values
            entry = {}
            for i, header in enumerate(headers):
                if i < len(parts):
                    # Clean up header names
                    clean_header = header.lower().replace("-", "_").replace("%", "percent")

                    # Try to convert numeric values
                    value = parts[i]
                    if clean_header not in [
                        "filesystem",
                        "mounted",
                        "on",
                        "mount_point",
                    ]:
                        try:
                            # Remove % sign if present
                            if value.endswith("%"):
                                value = value[:-1]

                            # Convert to number if possible
                            if "." in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass  # Keep as string if conversion fails

                    entry[clean_header] = value

            # Handle "Mounted on" special case which often appears as two separate headers
            if "on" in entry and "mounted" in entry:
                entry["mount_point"] = entry["on"]
                del entry["on"]
                del entry["mounted"]

            # Add a version marker
            entry["parser_version"] = "8.x"

            results.append(entry)

        return results

    def _parse_output_v9(self, raw_output: str) -> List[Dict[str, Any]]:
        """
        Parser specific to df version 9.x (GNU coreutils)
        Newer versions might have additional features or different formats
        """
        # Start with the v8 parser as a base
        results = self._parse_output_v8(raw_output)

        # Add enhancements specific to v9
        for entry in results:
            # Add version marker
            entry["parser_version"] = "9.x"

            # Calculate additional metrics that might be available in newer versions
            if (
                "size" in entry
                and "used" in entry
                and isinstance(entry["size"], (int, float))
                and isinstance(entry["used"], (int, float))
            ):
                # Calculate usage ratio (different format than use_percent)
                entry["usage_ratio"] = entry["used"] / entry["size"] if entry["size"] > 0 else 0

        return results

    # Methods specific to df
    def get_filesystem_usage(self, mount_point: str = "/") -> Dict[str, Any]:
        """
        Get disk usage information for a specific mount point

        Args:
            mount_point: Path to the mount point (default: root "/")

        Returns:
            Dictionary with filesystem usage information
        """
        # Create command context
        context = CommandContext()

        # Build command with specific mount point
        original_command_builder = self.build_command
        self.build_command = lambda: f"df -h {mount_point}"

        try:
            # Execute command
            result = self.execute(context)

            # Extract information for the specific mount point
            if result.success and result.structured_output:
                for fs_info in result.structured_output:
                    if fs_info.get("mount_point") == mount_point:
                        return fs_info

                # If we didn't find an exact match, return the first entry
                return result.structured_output[0]
            else:
                return {}
        finally:
            # Restore original command builder
            self.build_command = original_command_builder

    def show_filesystem(self, filesystem: str) -> "DfCommand":
        """
        Specifies a filesystem to display

        Args:
            filesystem: Path to the filesystem to display

        Returns:
            Self for method chaining
        """
        return self.add_arg(filesystem)

    def build_command(self) -> str:
        """Builds the df command string with human-readable format"""
        return "df -h"

    def human_readable(self) -> "DfCommand":
        """Option -h - shows sizes in human-readable format"""
        return self.with_option("-h")

    def inodes(self) -> "DfCommand":
        """Option -i - shows inode information instead of block information"""
        return self.with_option("-i")

    def type(self, fs_type: str) -> "DfCommand":
        """Option -t - shows only filesystems of specified type"""
        return self.with_param("t", fs_type)

    def exclude_type(self, fs_type: str) -> "DfCommand":
        """Option -x - excludes filesystems of specified type"""
        return self.with_param("x", fs_type)
