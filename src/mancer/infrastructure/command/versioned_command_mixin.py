import logging
import re
from typing import Any, Callable, ClassVar, Dict, Optional

from ...domain.model.command_context import CommandContext
from ...domain.model.tool_version import ToolVersion
from ...domain.service.tool_version_service import ToolVersionService

logger = logging.getLogger(__name__)


class VersionedCommandMixin:
    """
    Mixin for implementing command versioning.
    Each command that inherits this mixin will check the system tool version
    before execution and emit a warning if the version is not on the whitelist.

    It also supports version-specific behavior through version adapters.
    """

    # System tool name (to be overridden in child classes)
    tool_name: ClassVar[str] = ""

    # Version adapters mapping
    # Maps version patterns to method names for version-specific behavior
    # Example: {"1.x": "_parse_output_v1", "2.x": "_parse_output_v2"}
    version_adapters: ClassVar[Dict[str, str]] = {}

    # Class-level tool version service
    _version_service: ClassVar[Optional[ToolVersionService]] = None

    @classmethod
    def get_version_service(cls) -> ToolVersionService:
        """
        Returns or initializes the tool version service
        """
        if cls._version_service is None:
            cls._version_service = ToolVersionService()
        return cls._version_service

    def check_tool_version(self, context: CommandContext) -> Optional[ToolVersion]:
        """
        Checks the system tool version and emits a warning if the version is not on the whitelist

        Args:
            context: Command execution context

        Returns:
            ToolVersion object or None if version detection failed
        """
        if not self.tool_name:
            logger.warning(f"Command {self.__class__.__name__} does not have a defined tool name")
            return None

        version_service = self.get_version_service()
        is_allowed, message = version_service.is_version_allowed(self.tool_name)

        if not is_allowed:
            logger.warning(message)

            # Save the warning in the context metadata for results
            warnings = context.get_parameter("warnings", [])
            warnings.append(message)
            context.set_parameter("warnings", warnings)

        # Return the detected tool version for potential version-specific behavior
        return version_service.detect_tool_version(self.tool_name)

    def get_version_specific_method(
        self, method_base_name: str, version: Optional[ToolVersion] = None
    ) -> Optional[Callable]:
        """
        Gets the appropriate method for the detected version using the version_adapters mapping

        Args:
            method_base_name: Base method name (e.g., "_parse_output")
            version: Detected tool version

        Returns:
            Method reference or None if no version-specific method found
        """
        if not version or not self.version_adapters:
            return None

        # Try to find adapter for the specific version
        for pattern, method_name in self.version_adapters.items():
            # Replace 'x' with wildcard in version pattern
            regex_pattern = pattern.replace(".x", r"\..*").replace("x", r".*")
            if re.match(regex_pattern, version.version):
                if hasattr(self, method_name):
                    return getattr(self, method_name)

        return None

    def adapt_to_version(self, version: Optional[ToolVersion], method_base_name: str, *args, **kwargs) -> Any:
        """
        Adapts behavior based on the detected version

        Args:
            version: Detected tool version
            method_base_name: Base method name to adapt
            *args, **kwargs: Arguments to pass to the method

        Returns:
            Result of the version-specific method or default method
        """
        if not version:
            # No version detected, use default method
            default_method = getattr(self, method_base_name, None)
            if default_method:
                return default_method(*args, **kwargs)
            return None

        # Check for version-specific method
        version_method = self.get_version_specific_method(method_base_name, version)
        if version_method:
            logger.debug(f"Using version-specific method for {self.tool_name} v{version.version}")
            return version_method(*args, **kwargs)

        # Fallback to default method
        default_method = getattr(self, method_base_name, None)
        if default_method:
            return default_method(*args, **kwargs)

        return None

    @classmethod
    def register_allowed_version(cls, version: str) -> None:
        """
        Registers an allowed version of the system tool

        Args:
            version: Allowed tool version
        """
        if not cls.tool_name:
            logger.warning(f"Command {cls.__name__} does not have a defined tool name")
            return

        version_service = cls.get_version_service()
        version_service.register_allowed_version(cls.tool_name, version)

    @classmethod
    def register_allowed_versions(cls, versions: list) -> None:
        """
        Registers multiple allowed versions of the system tool

        Args:
            versions: List of allowed tool versions
        """
        if not cls.tool_name:
            logger.warning(f"Command {cls.__name__} does not have a defined tool name")
            return

        version_service = cls.get_version_service()
        version_service.register_allowed_versions(cls.tool_name, versions)
