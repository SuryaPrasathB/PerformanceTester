import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.test_engine.test_builder import TestBuilder
from core.test_engine.test_context import TestContext

class TestLoopCaching(unittest.TestCase):
    def test_loop_prompt_caching(self):
        # Create a mock DeviceManager
        mock_dm = MagicMock()
        
        # Instantiate a TestContext with mock DeviceManager and mock config
        mock_config = {
            "testing": {
                "min_step_duration_s": 0.0  # Set to 0 to speed up execution
            }
        }
        
        ctx = TestContext(mock_dm, config=mock_config)
        
        # Mock the hardware service
        mock_hw = MagicMock()
        ctx.hardware_service = mock_hw
        
        # We will track how many times the prompt callback is actually called
        prompt_calls = []
        
        def mock_prompt_callback(msg, req_input):
            prompt_calls.append(msg)
            # Simulate user entering input
            ctx.user_input_result = f"InputFor_{msg}"
            ctx.user_action_event.set()
            
        ctx._prompt_callback = mock_prompt_callback
        
        # Build a test builder sequence
        builder = TestBuilder()
        
        # A simple loop repeated 3 times
        def loop_body(b, idx):
            # Prompt 1 (requires input, saves value)
            b.prompt_user("Enter category", requires_input=True, save_as=f"category_val_{idx}")
            # Prompt 2 (no input required)
            b.prompt_user("Please confirm load", requires_input=False)
            
        builder.loop(3, loop_body)
        
        # Run the builder
        builder.execute(ctx)
        
        # Assertions
        # 1. The prompts should have only been shown once (the first iteration, idx=0)
        # So we expect prompt_calls to contain exactly: ["Enter category", "Please confirm load"]
        print("Prompt calls received:", prompt_calls)
        self.assertEqual(len(prompt_calls), 2)
        self.assertEqual(prompt_calls[0], "Enter category")
        self.assertEqual(prompt_calls[1], "Please confirm load")
        
        # 2. Let's verify that the values were successfully stored in ctx.runtime_values
        # For iteration 0, it should be InputFor_Enter category
        # For iterations 1 and 2, they should also have the same value because of cached retrieval!
        self.assertEqual(ctx.get_runtime_value("category_val_0"), "InputFor_Enter category")
        self.assertEqual(ctx.get_runtime_value("category_val_1"), "InputFor_Enter category")
        self.assertEqual(ctx.get_runtime_value("category_val_2"), "InputFor_Enter category")
        print("Runtime values saved correctly!")

if __name__ == "__main__":
    unittest.main()
