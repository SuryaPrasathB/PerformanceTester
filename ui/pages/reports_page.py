from PySide6.QtWidgets import QWidget
from ui.pages.ui_reports_page import Ui_ReportsPage

class ReportsPage(QWidget, Ui_ReportsPage):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
