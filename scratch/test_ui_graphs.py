import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Initialize QApplication (required for QWidget creation)
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from ui.pages.test_page import TestPage

class TestUiGraphs(unittest.TestCase):
    def test_graphs_placeholder_and_limit(self):
        mock_dm = MagicMock()
        mock_mw = MagicMock()
        
        # Instantiate the TestPage widget
        page = TestPage(mock_dm, mock_mw)
        
        # 1. Verify initial state: placeholder visible, dynamic_cards empty
        self.assertFalse(page.lbl_graphs_placeholder.isHidden())
        self.assertEqual(len(page.dynamic_cards), 0)
        self.assertEqual(page.horizontalLayout_graphs.alignment(), Qt.AlignCenter)
        
        # 2. Add first waveform card
        page.add_waveform_card("Waveform 1", [1, 2, 3], 1, 1)
        self.assertTrue(page.lbl_graphs_placeholder.isHidden())
        self.assertEqual(len(page.dynamic_cards), 1)
        
        # 3. Add second and third cards
        page.add_waveform_card("Waveform 2", [4, 5, 6], 1, 1)
        page.add_waveform_card("Waveform 3", [7, 8, 9], 1, 1)
        self.assertEqual(len(page.dynamic_cards), 3)
        self.assertEqual(page.dynamic_cards[0].name, "Waveform 1")
        self.assertEqual(page.dynamic_cards[1].name, "Waveform 2")
        self.assertEqual(page.dynamic_cards[2].name, "Waveform 3")
        
        # 4. Add a fourth card - oldest (Waveform 1) should be removed/deleted
        page.add_waveform_card("Waveform 4", [10, 11, 12], 1, 1)
        self.assertEqual(len(page.dynamic_cards), 3)
        self.assertEqual(page.dynamic_cards[0].name, "Waveform 2")
        self.assertEqual(page.dynamic_cards[1].name, "Waveform 3")
        self.assertEqual(page.dynamic_cards[2].name, "Waveform 4")
        
        # 5. Verify starting a new test resets placeholder visibility and clears cards
        # Mock class/item selection for start_test
        page.list_tests = MagicMock()
        selected_item = MagicMock()
        selected_item.data.return_value = "G2NormalOperationTest"
        page.list_tests.selectedItems.return_value = [selected_item]
        page.cmb_meter_profile = MagicMock()
        page.cmb_meter_profile.currentData.return_value = {}
        
        # Call start_test (it might raise some runner/init exception due to mocks,
        # but the card clearance and placeholder show logic happens before running)
        try:
            page.start_test()
        except Exception:
            pass
            
        self.assertFalse(page.lbl_graphs_placeholder.isHidden())
        self.assertEqual(len(page.dynamic_cards), 0)
        print("UI Graph tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
