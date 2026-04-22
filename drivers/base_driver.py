from abc import ABC, abstractmethod
import logging

class BaseDriver(ABC):
    """
    Abstract base class for all protocol drivers.
    Defines the standard interface for hardware communication.
    """
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.is_connected = False
        self.mock_mode = config.get("mock", False)
        
    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection to the hardware device."""
        pass
        
    @abstractmethod
    def disconnect(self) -> bool:
        """Closes the connection to the hardware device."""
        pass
        
    @abstractmethod
    def read_data(self, *args, **kwargs) -> any:
        """Reads data from the hardware device."""
        pass
        
    @abstractmethod
    def write_data(self, data: any, *args, **kwargs) -> bool:
        """Writes data to the hardware device."""
        pass
