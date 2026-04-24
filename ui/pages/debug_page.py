from PySide6.QtWidgets import QWidget
from ui.pages.ui_debug_page import Ui_DebugPage

class DebugPage(QWidget, Ui_DebugPage):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
