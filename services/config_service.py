import json
import os
from typing import Dict, Any

class ConfigService:
    """
    ConfigService handles loading configuration data from JSON files.
    """
    def __init__(self, config_path: str = "configs/device_config.json"):
        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from the file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
            
        with open(self.config_path, "r") as f:
            self._config_data = json.load(f)
            
        return self._config_data
        
    def get_config(self) -> Dict[str, Any]:
        """Returns the loaded configuration. If not loaded, it attempts to load it."""
        if not self._config_data:
            return self.load_config()
        return self._config_data
        
    def get_devices(self) -> list:
        """Returns the list of devices from the configuration."""
        config = self.get_config()
        return config.get("devices", [])
        
    def get_database_config(self) -> Dict[str, Any]:
        """Returns the database configuration."""
        config = self.get_config()
        return config.get("database", {})
