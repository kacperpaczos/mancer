import json
import logging
import os
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration manager for the Mancer framework.
    Responsible for loading settings from configuration files and making them available to other components.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """Singleton implementation for ConfigManager"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager"""
        if self._initialized:
            return

        # Dictionary storing configuration
        self._config: Dict[str, Any] = {
            "tool_versions": {},  # Allowed tool versions
            "settings": {},  # General settings
            "paths": {},  # Resource paths
        }

        # Paths to configuration files
        self._config_paths = {
            "tool_versions": self._find_config_path("tool_versions.yaml"),
            "settings": self._find_config_path("settings.yaml"),
        }

        # Load configuration
        self._load_config()

        self._initialized = True

    def _find_config_path(self, filename: str) -> str:
        """
        Finds the path to a configuration file by searching in several standard locations.

        Args:
            filename: Configuration file name

        Returns:
            Path to the configuration file or an empty string if not found
        """
        # Search order:
        # 1. Current directory
        # 2. ~/.mancer/ directory
        # 3. /etc/mancer/
        # 4. Package directory mancer/config

        # Check current directory
        if os.path.exists(filename):
            return os.path.abspath(filename)

        # Check ~/.mancer/ directory
        home_config = os.path.expanduser(f"~/.mancer/{filename}")
        if os.path.exists(home_config):
            return home_config

        # Check /etc/mancer/
        system_config = f"/etc/mancer/{filename}"
        if os.path.exists(system_config):
            return system_config

        # Check package directory
        package_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        package_config = os.path.join(package_dir, "config", filename)
        if os.path.exists(package_config):
            return package_config

        # If not found, return path in current directory
        return filename

    def _load_config(self) -> None:
        """Loads configuration from files"""
        # Loading tool versions
        self._load_tool_versions()

        # Loading general settings
        self._load_settings()

    def _load_tool_versions(self) -> None:
        """Loads configuration of allowed tool versions"""
        config_path = self._config_paths["tool_versions"]

        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                        versions_config = yaml.safe_load(file)
                    elif config_path.endswith(".json"):
                        versions_config = json.load(file)
                    else:
                        logger.warning(f"Unsupported configuration file format: {config_path}")
                        return

                self._config["tool_versions"] = versions_config
                logger.info(f"Loaded tool versions configuration from {config_path}")
            else:
                # If file doesn't exist, create default configuration
                self._create_default_tool_versions_config()

        except Exception as e:
            logger.error(f"Error loading tool versions configuration: {str(e)}")
            # Load default configuration in case of error
            self._create_default_tool_versions_config()

    def _load_settings(self) -> None:
        """Loads general settings"""
        config_path = self._config_paths["settings"]

        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                        settings = yaml.safe_load(file)
                    elif config_path.endswith(".json"):
                        settings = json.load(file)
                    else:
                        logger.warning(f"Unsupported configuration file format: {config_path}")
                        return

                self._config["settings"] = settings
                logger.info(f"Loaded settings from {config_path}")
            else:
                logger.info(f"Settings file {config_path} does not exist, using default settings")

        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")

    def _create_default_tool_versions_config(self) -> None:
        """Creates default configuration of allowed tool versions"""
        default_config = {
            "tools": {
                # GNU Coreutils
                "ls": ["8.30", "8.31", "8.32", "9.0", "9.1"],
                "cat": ["8.30", "8.31", "8.32", "9.0", "9.1"],
                "echo": ["8.30", "8.31", "8.32", "9.0", "9.1"],
                "find": ["4.7.0", "4.8.0", "4.9.0"],
                # GNU Grep
                "grep": ["3.1", "3.4", "3.5", "3.6", "3.7"],
                # Procps-ng
                "ps": ["3.3.15", "3.3.16", "3.3.17"],
                # Util-linux
                "df": ["2.34", "2.35", "2.36", "2.37", "2.38"],
                # Systemd
                "systemctl": ["239", "245", "247", "249", "250", "251", "252"],
                # Hostname
                "hostname": ["3.21", "3.22", "3.23"],
                # wc
                "wc": ["8.30", "8.31", "8.32", "9.0", "9.1"],
            }
        }

        self._config["tool_versions"] = default_config

        # Save default configuration to file
        config_path = self._config_paths["tool_versions"]
        config_dir = os.path.dirname(config_path)

        try:
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(config_path, "w") as file:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    yaml.dump(default_config, file, default_flow_style=False)
                elif config_path.endswith(".json"):
                    json.dump(default_config, file, indent=2)
                else:
                    with open(f"{config_path}.yaml", "w") as yaml_file:
                        yaml.dump(default_config, yaml_file, default_flow_style=False)

            logger.info(f"Created default tool versions configuration in {config_path}")

        except Exception as e:
            logger.error(f"Error creating default tool versions configuration: {str(e)}")

    def get_allowed_tool_versions(self, tool_name: str) -> List[str]:
        """
        Returns allowed versions for a given tool

        Args:
            tool_name: Tool name

        Returns:
            List of allowed versions or empty list if the tool is not configured
        """
        try:
            return self._config["tool_versions"]["tools"].get(tool_name, [])
        except Exception:
            return []

    def add_allowed_tool_version(self, tool_name: str, version: str) -> None:
        """
        Adds an allowed tool version to the configuration

        Args:
            tool_name: Tool name
            version: Tool version
        """
        if "tools" not in self._config["tool_versions"]:
            self._config["tool_versions"]["tools"] = {}

        if tool_name not in self._config["tool_versions"]["tools"]:
            self._config["tool_versions"]["tools"][tool_name] = []

        if version not in self._config["tool_versions"]["tools"][tool_name]:
            self._config["tool_versions"]["tools"][tool_name].append(version)
            self._save_tool_versions_config()

    def set_allowed_tool_versions(self, tool_name: str, versions: List[str]) -> None:
        """
        Sets allowed tool versions

        Args:
            tool_name: Tool name
            versions: List of allowed versions
        """
        if "tools" not in self._config["tool_versions"]:
            self._config["tool_versions"]["tools"] = {}

        self._config["tool_versions"]["tools"][tool_name] = versions
        self._save_tool_versions_config()

    def _save_tool_versions_config(self) -> None:
        """Saves configuration of allowed tool versions to file"""
        config_path = self._config_paths["tool_versions"]

        try:
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(config_path, "w") as file:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    yaml.dump(self._config["tool_versions"], file, default_flow_style=False)
                elif config_path.endswith(".json"):
                    json.dump(self._config["tool_versions"], file, indent=2)
                else:
                    with open(f"{config_path}.yaml", "w") as yaml_file:
                        yaml.dump(
                            self._config["tool_versions"],
                            yaml_file,
                            default_flow_style=False,
                        )

            logger.info(f"Saved tool versions configuration to {config_path}")

        except Exception as e:
            logger.error(f"Error saving tool versions configuration: {str(e)}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Returns a setting value

        Args:
            key: Setting key
            default: Default value if the setting doesn't exist

        Returns:
            Setting value or default value if the setting doesn't exist
        """
        try:
            # Handling nested keys (e.g., "logging.level")
            keys = key.split(".")
            value = self._config["settings"]

            for k in keys:
                value = value.get(k)
                if value is None:
                    return default

            return value
        except Exception:
            return default

    def set_setting(self, key: str, value: Any) -> None:
        """
        Sets a setting value

        Args:
            key: Setting key
            value: Setting value
        """
        # Handling nested keys (e.g., "logging.level")
        keys = key.split(".")

        # Last key in the chain
        last_key = keys[-1]

        # Remaining keys (path to the last key)
        path_keys = keys[:-1]

        # Reference to the current place in the configuration tree
        current = self._config["settings"]

        # Navigate to the appropriate place in the configuration tree
        for k in path_keys:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set value
        current[last_key] = value

        # Save configuration
        self._save_settings_config()

    def _save_settings_config(self) -> None:
        """Saves general settings to file"""
        config_path = self._config_paths["settings"]

        try:
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(config_path, "w") as file:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    yaml.dump(self._config["settings"], file, default_flow_style=False)
                elif config_path.endswith(".json"):
                    json.dump(self._config["settings"], file, indent=2)
                else:
                    with open(f"{config_path}.yaml", "w") as yaml_file:
                        yaml.dump(
                            self._config["settings"],
                            yaml_file,
                            default_flow_style=False,
                        )

            logger.info(f"Saved settings to {config_path}")

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
