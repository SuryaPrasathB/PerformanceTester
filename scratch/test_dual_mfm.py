import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.device_manager import DeviceManager
from services.hardware_service import HardwareService
from core.test_engine.test_context import TestContext
from drivers.modbus_driver import ModbusDriver

class TestDualMFM(unittest.TestCase):
    def setUp(self):
        # Mock logger
        self.logger = MagicMock()
        
        # Define mock configuration with 2 MFM meters sharing COM1
        self.config_data = {
            "devices": [
                {
                    "name": "PLC1",
                    "type": "modbus",
                    "ip": "192.168.0.118",
                    "port": 502,
                    "mock": True
                },
                {
                    "name": "MFMMeter1",
                    "type": "modbus",
                    "port": "COM1",
                    "baudrate": 9600,
                    "slave_id": 1,
                    "mock": True
                },
                {
                    "name": "MFMMeter2",
                    "type": "modbus",
                    "port": "COM1",
                    "baudrate": 9600,
                    "slave_id": 2,
                    "mock": True
                }
            ],
            "plc": {},
            "safety": {}
        }
        
        # Mock ConfigService
        self.config_service = MagicMock()
        self.config_service.get_config.return_value = self.config_data
        self.config_service.get_devices.return_value = self.config_data["devices"]

    def test_driver_instantiation_and_slave_id(self):
        # 1. Instantiate DeviceManager
        dm = DeviceManager(self.config_service, self.logger)
        
        # Check drivers exist
        self.assertIn("MFMMeter1", dm.drivers)
        self.assertIn("MFMMeter2", dm.drivers)
        
        drv1 = dm.drivers["MFMMeter1"]
        drv2 = dm.drivers["MFMMeter2"]
        
        self.assertIsInstance(drv1, ModbusDriver)
        self.assertIsInstance(drv2, ModbusDriver)
        
        # Check slave_id properties parsed correctly
        self.assertEqual(drv1.slave_id, 1)
        self.assertEqual(drv2.slave_id, 2)
        
        # Check shared lock (since they both use COM1)
        self.assertIs(drv1._lock, drv2._lock)
        
        # Cleanup
        dm.cleanup()

    def test_hardware_service_routing_non_g7(self):
        # 1. Instantiate DeviceManager & Context
        dm = DeviceManager(self.config_service, self.logger)
        ctx = TestContext(dm)
        ctx.test_identifier = "g3"  # Non-G7 test
        
        hw = ctx.hardware_service
        
        # Connect drivers in mock mode
        hw.mfm_drv.connect()
        hw.mfm2_drv.connect()
        
        # Mock read_float methods on both drivers
        hw.mfm_drv.read_float = MagicMock(return_value=123.4)
        hw.mfm2_drv.read_float = MagicMock(return_value=999.9)
        
        # Read telemetry
        telemetry = hw.read_mfm_telemetry()
        
        # In non-G7 (g3), both voltage, current, and PF should poll MFMMeter1
        # Hence the current should be from MFMMeter1 (123.4), not MFMMeter2 (999.9)
        self.assertEqual(telemetry["voltage"], 123.4)
        self.assertEqual(telemetry["current"], 123.4)
        self.assertEqual(telemetry["power_factor"], 123.4)
        
        from core.hardware_mapping import MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
        swap_v = (MFM_REGISTER_TYPES.get("VOLTAGE", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        swap_i = (MFM_REGISTER_TYPES.get("CURRENT", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        swap_pf = (MFM_REGISTER_TYPES.get("PF", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        hw.mfm_drv.read_float.assert_any_call(40001, function_code=MFM_FUNCTION_CODE, swapped=swap_v)
        hw.mfm_drv.read_float.assert_any_call(40003, function_code=MFM_FUNCTION_CODE, swapped=swap_i)
        hw.mfm_drv.read_float.assert_any_call(40005, function_code=MFM_FUNCTION_CODE, swapped=swap_pf)
        hw.mfm2_drv.read_float.assert_not_called()
        
        # Cleanup
        dm.cleanup()

    def test_hardware_service_routing_g7(self):
        # 1. Instantiate DeviceManager & Context
        dm = DeviceManager(self.config_service, self.logger)
        ctx = TestContext(dm)
        ctx.test_identifier = "g7"  # G7 test
        
        hw = ctx.hardware_service
        
        # Connect drivers in mock mode
        hw.mfm_drv.connect()
        hw.mfm2_drv.connect()
        
        # Mock read_float methods
        hw.mfm_drv.read_float = MagicMock(side_effect=lambda addr, **kwargs: 240.0 if addr == 40001 else 0.95)
        hw.mfm2_drv.read_float = MagicMock(return_value=0.045)  # mA meter
        
        # Read telemetry
        telemetry = hw.read_mfm_telemetry()
        
        # In G7, voltage & PF should poll MFMMeter1, current should poll MFMMeter2
        self.assertEqual(telemetry["voltage"], 240.0)
        self.assertEqual(telemetry["current"], 0.045)
        self.assertEqual(telemetry["power_factor"], 0.95)
        
        from core.hardware_mapping import MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
        swap_v = (MFM_REGISTER_TYPES.get("VOLTAGE", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        swap_i = (MFM_REGISTER_TYPES.get("CURRENT", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        swap_pf = (MFM_REGISTER_TYPES.get("PF", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
        hw.mfm_drv.read_float.assert_any_call(40001, function_code=MFM_FUNCTION_CODE, swapped=swap_v)
        hw.mfm_drv.read_float.assert_any_call(40005, function_code=MFM_FUNCTION_CODE, swapped=swap_pf)
        hw.mfm2_drv.read_float.assert_called_with(40003, function_code=MFM_FUNCTION_CODE, swapped=swap_i)
        
        # Cleanup
        dm.cleanup()

if __name__ == "__main__":
    unittest.main()
