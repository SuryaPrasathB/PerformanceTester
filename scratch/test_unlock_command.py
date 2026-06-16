import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.test_engine.test_builder import TestBuilder
from core.test_engine.test_context import TestContext

class TestUnlockCommand(unittest.TestCase):
    def test_automatic_unlock_before_switch(self):
        # Create a mock DeviceManager
        mock_dm = MagicMock()
        
        # Instantiate a TestContext with mock DeviceManager
        mock_config = {
            "testing": {
                "min_step_duration_s": 0.0
            }
        }
        ctx = TestContext(mock_dm, config=mock_config)
        
        # Setup active profile with unlock and close_load_switch mapped
        mock_profile = {
            "id": "test_profile",
            "name": "Test Serial Profile",
            "communication_mode": "Serial",
            "commands": {
                "unlock": {
                    "value": "7E A0 0A 03 21 93 0F 04 7E",
                    "format": "Hex",
                    "expected_response": "7E A0",
                    "expected_terminator": "7E"
                },
                "close_load_switch": {
                    "value": "7E A0 08 03 21 93 0F 02 7E",
                    "format": "Hex",
                    "expected_response": "7E A0",
                    "expected_terminator": "7E"
                },
                "read_serial_number": {
                    "value": "7E A0 07 03 21 93 0F 01 7E",
                    "format": "Hex",
                    "expected_response": "7E A0",
                    "expected_terminator": "7E"
                }
            }
        }
        ctx.meter_profile = mock_profile
        
        # Mock serial driver write/read
        mock_serial_drv = MagicMock()
        mock_serial_drv.__class__.__name__ = "SerialDriver"
        mock_serial_drv.is_connected = True
        mock_serial_drv.serial_conn = MagicMock()
        
        sent_payloads = []
        def mock_write(payload):
            sent_payloads.append(payload)
            return True
            
        mock_serial_drv.write_data = mock_write
        
        # Mock read_until to return expected response
        # Since expected responses are '7E A0', let's return it
        mock_serial_drv.read_until = MagicMock(return_value=bytes.fromhex("7EA0"))
        
        ctx.hardware_service = MagicMock()
        ctx.hardware_service.energymeter_drv = mock_serial_drv
        
        # 1. Execute close_load_switch command
        builder = TestBuilder()
        builder.send_meter_command("close_load_switch")
        builder.execute(ctx)
        
        # Verify both unlock and close_load_switch payloads were sent in order
        expected_unlock_payload = bytes.fromhex("7EA00A0321930F047E")
        expected_close_payload = bytes.fromhex("7EA0080321930F027E")
        
        self.assertEqual(len(sent_payloads), 2)
        self.assertEqual(sent_payloads[0], expected_unlock_payload)
        self.assertEqual(sent_payloads[1], expected_close_payload)
        print("Success: Unlock command sent before close_load_switch!")
        
        # 2. Reset and test read_serial_number (should NOT send unlock)
        sent_payloads.clear()
        builder2 = TestBuilder()
        builder2.send_meter_command("read_serial_number")
        builder2.execute(ctx)
        
        expected_read_serial_payload = bytes.fromhex("7EA0070321930F017E")
        self.assertEqual(len(sent_payloads), 1)
        self.assertEqual(sent_payloads[0], expected_read_serial_payload)
        print("Success: Unlock command NOT sent for read_serial_number!")
        
        # 3. Test profile without unlock mapped
        sent_payloads.clear()
        profile_no_unlock = {
            "id": "test_profile_no_unlock",
            "name": "Test Serial Profile No Unlock",
            "communication_mode": "Serial",
            "commands": {
                "close_load_switch": {
                    "value": "7E A0 08 03 21 93 0F 02 7E",
                    "format": "Hex"
                }
            }
        }
        ctx.meter_profile = profile_no_unlock
        builder3 = TestBuilder()
        builder3.send_meter_command("close_load_switch")
        builder3.execute(ctx)
        
        # Since it is format Hex, no write terminator should be appended!
        expected_close_payload_no_term = bytes.fromhex("7EA0080321930F027E")
        self.assertEqual(len(sent_payloads), 1)
        self.assertEqual(sent_payloads[0], expected_close_payload_no_term)
        print("Success: HEX format command sent without appending terminator!")

    def test_write_terminator_handling(self):
        mock_dm = MagicMock()
        mock_config = {"testing": {"min_step_duration_s": 0.0}}
        ctx = TestContext(mock_dm, config=mock_config)
        
        mock_profile = {
            "id": "test_profile_term",
            "name": "Test Terminator Profile",
            "communication_mode": "Serial",
            "serial_settings": {
                "baudrate": 9600,
                "timeout": 2.0,
                "write_terminator": "\\r"
            },
            "commands": {
                "unlock": {
                    "value": "PrGunlock",
                    "format": "ASCII"
                },
                "close_load_switch": {
                    "value": "rEL1<CR>",
                    "format": "ASCII"
                }
            }
        }
        ctx.meter_profile = mock_profile
        
        mock_serial_drv = MagicMock()
        mock_serial_drv.__class__.__name__ = "SerialDriver"
        mock_serial_drv.is_connected = True
        mock_serial_drv.serial_conn = MagicMock()
        
        sent_payloads = []
        mock_serial_drv.write_data = lambda payload: sent_payloads.append(payload) or True
        mock_serial_drv.read_until = MagicMock(return_value=bytes.fromhex("7EA0"))
        
        ctx.hardware_service = MagicMock()
        ctx.hardware_service.energymeter_drv = mock_serial_drv
        
        # Send unlock (should append \r because it has no terminator)
        builder = TestBuilder()
        builder.send_meter_command("unlock")
        builder.execute(ctx)
        self.assertEqual(sent_payloads[-1], b"PrGunlock\r")
        print("Success: Appended \\r terminator to 'PrGunlock'!")
        
        # Send close_load_switch (should replace <CR> with \r and NOT append another \r)
        builder2 = TestBuilder()
        builder2.send_meter_command("close_load_switch")
        builder2.execute(ctx)
        self.assertEqual(sent_payloads[-1], b"rEL1\r")
        print("Success: Handled 'rEL1<CR>' by replacing and not duplicating terminator!")

if __name__ == "__main__":
    unittest.main()
