from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class DeviceModel:
    """
    DeviceModel represents the metadata for a single device.
    """
    name: str
    type: str
    connection_details: Dict[str, Any] = field(default_factory=dict)
    mock: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceModel':
        """
        Creates a DeviceModel instance from a dictionary (e.g., from config).
        """
        # Extract common fields
        name = data.get("name", "Unknown")
        device_type = data.get("type", "unknown")
        mock = data.get("mock", False)
        
        # Everything else is considered connection details
        connection_details = {k: v for k, v in data.items() if k not in ("name", "type", "mock")}
        
        return cls(
            name=name,
            type=device_type,
            connection_details=connection_details,
            mock=mock
        )
