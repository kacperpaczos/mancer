import os
import json
from typing import Dict, Any, Optional

class Proficer:
    def __init__(self, profiles_dir: str = "profiles", default_profile: Optional[Dict[str, Any]] = None):
        self.profiles_dir = profiles_dir
        self.current_profile = None
        self.default_schema = {
            "connection": {
                "name": "",
                "host": "",
                "username": "",
                "password": "",
                "port": 22,
                "timeout": 30,
                "key_filename": None
            }
        }
        
        if default_profile:
            self._validate_profile(default_profile)
            self.default_schema = default_profile
            
        self._initialize_profiles()
    
    def _initialize_profiles(self) -> None:
        """Initialize the profiles system."""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
            
        default_path = os.path.join(self.profiles_dir, "default.json")
        if not os.path.exists(default_path):
            with open(default_path, 'w', encoding='utf-8') as f:
                json.dump(self.default_schema, f, indent=4)
    
    def _validate_profile(self, profile: Dict[str, Any]) -> None:
        """Check if profile contains all required fields from the schema."""
        def check_keys(schema: Dict[str, Any], data: Dict[str, Any], path: str = ""):
            for key, value in schema.items():
                current_path = f"{path}.{key}" if path else key
                if key not in data:
                    raise ValueError(f"Missing required field: {current_path}")
                if isinstance(value, dict):
                    if not isinstance(data[key], dict):
                        raise ValueError(f"Field {current_path} must be a dictionary")
                    check_keys(value, data[key], current_path)
        
        check_keys(self.default_schema, profile)
    
    def load_profile(self, profile_name: str = "default") -> Dict[str, Any]:
        """Load profile by name."""
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                self._validate_profile(profile_data)
                self.current_profile = profile_data
            return self.current_profile
        except FileNotFoundError:
            raise FileNotFoundError(f"Profile {profile_name} does not exist.")
    
    def save_profile(self, data: Dict[str, Any], profile_name: str = "default") -> None:
        """Save profile with given name."""
        self._validate_profile(data)
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        self.current_profile = data
    
    def update_schema(self, new_schema: Dict[str, Any]) -> None:
        """Update default profile schema."""
        self.default_schema = new_schema
    
    def get_current_profile(self) -> Optional[Dict[str, Any]]:
        """Return currently loaded profile."""
        return self.current_profile

    def generate_profile(self, **kwargs) -> Dict[str, Any]:
        """Generate new profile based on provided arguments.
        
        Example:
        generate_profile(
            name="server1",
            host="example.com",
            username="user",
            password="pass"
        )
        """
        new_profile = {}
        
        def fill_schema(schema: Dict[str, Any], target: Dict[str, Any]):
            for key, value in schema.items():
                if isinstance(value, dict):
                    target[key] = {}
                    fill_schema(value, target[key])
                else:
                    flat_key = key.replace(".", "_")
                    target[key] = kwargs.get(key, value)
        
        fill_schema(self.default_schema, new_profile)
        self._validate_profile(new_profile)
        return new_profile
