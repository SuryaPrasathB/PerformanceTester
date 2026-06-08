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

    def save_config(self, new_config_data: Dict[str, Any]) -> bool:
        """Saves the provided configuration dictionary to the JSON file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(new_config_data, f, indent=2)
            self._config_data = new_config_data
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def update_device(self, device_name: str, new_params: Dict[str, Any]) -> bool:
        """Updates specific parameters of a device and saves the configuration."""
        config = self.get_config()
        devices = config.get("devices", [])
        
        updated = False
        for i, dev in enumerate(devices):
            if dev.get("name") == device_name:
                devices[i].update(new_params)
                updated = True
                break
                
        if updated:
            config["devices"] = devices
            return self.save_config(config)
        return False
