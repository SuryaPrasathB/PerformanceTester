from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot
from ui.pages.ui_logs_page import Ui_LogsPage

class LogsPage(QWidget, Ui_LogsPage):
    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)
        self.main_window = main_window

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        # High contrast colors on light background
        color = "#0F172A" 
        if level == "ERROR": 
            color = "#DC2626"
        elif level == "WARNING": 
            color = "#D97706"
            
        html_msg = f'<span style="color:{color};">{message}</span><br>'
        self.txt_logs.insertHtml(html_msg)
        
        scrollbar = self.txt_logs.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
