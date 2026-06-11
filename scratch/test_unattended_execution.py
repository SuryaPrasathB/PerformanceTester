import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.test_engine.test_runner import TestRunner
from core.test_engine.test_context import TestContext

class TestUnattendedExecution(unittest.TestCase):
    def test_database_session_no_prompts(self):
        mock_dm = MagicMock()
        mock_db = MagicMock()
        mock_dm.database_service = mock_db
        
        ctx = TestContext(mock_dm)
        ctx.meter_serial_number = "12345_TEST_SERIAL"
        
        # We will track if prompt_user_action is called
        ctx.prompt_user_action = MagicMock(side_effect=Exception("prompt_user_action should not be called!"))
        
        mock_test = MagicMock()
        mock_test.test_identifier = "G5"
        
        runner = TestRunner(mock_test, ctx)
        
        # Case 1: No existing record found - should create a new record
        mock_db.find_latest_incomplete_record.return_value = None
        mock_db.create_new_record.return_value = 101
        
        runner._handle_database_session()
        
        self.assertEqual(ctx.db_row_id, 101)
        mock_db.create_new_record.assert_called_with("12345_TEST_SERIAL")
        ctx.prompt_user_action.assert_not_called()
        
        # Reset mock calls
        mock_db.reset_mock()
        ctx.prompt_user_action.reset_mock()
        
        # Case 2: Existing incomplete record found - should automatically append
        mock_db.find_latest_incomplete_record.return_value = 202
        
        runner._handle_database_session()
        
        self.assertEqual(ctx.db_row_id, 202)
        mock_db.create_new_record.assert_not_called()
        ctx.prompt_user_action.assert_not_called()
        
        print("Unattended database session tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
