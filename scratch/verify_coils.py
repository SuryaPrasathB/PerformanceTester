import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.config_service import ConfigService
from drivers.modbus_driver import ModbusDriver
import unittest
from unittest.mock import MagicMock

class TestModbusCoils(unittest.TestCase):
    def setUp(self):
        self.config_service = ConfigService()
        self.config_service.load_config()
        self.plc_config = self.config_service.get_devices()[0] # PLC1

    def test_config_ip(self):
        # Verify PLC1 IP is aligned with the new IP 192.168.0.123
        self.assertEqual(self.plc_config.get("ip"), "192.168.0.123")
        self.assertEqual(self.plc_config.get("name"), "PLC1")

    def test_mock_read_write_coil(self):
        # Create driver in mock mode to check simulated states
        mock_driver_config = self.plc_config.copy()
        mock_driver_config["mock"] = True
        
        logger = MagicMock()
        driver = ModbusDriver(mock_driver_config, logger)
        driver.connect()
        
        # Test default read
        val = driver.read_coil(address=0x01)
        self.assertFalse(val)
        
        # Test write
        success = driver.write_coil(address=0x01, value=True)
        self.assertTrue(success)
        
        # Test read-back
        val = driver.read_coil(address=0x01)
        self.assertTrue(val)

if __name__ == "__main__":
    unittest.main()
