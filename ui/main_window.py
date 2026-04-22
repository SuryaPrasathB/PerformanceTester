from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QColor

class MainWindow(QMainWindow):
    """
    Main UI Window for the Meter Test System.
    """
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        
        self.setWindowTitle("Meter Test System")
        self.resize(800, 600)
        
        self._setup_ui()
        self._populate_devices()
        
    def _setup_ui(self):
        """Sets up the UI layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Device Status Panel ---
        status_label = QLabel("<b>Device Status Panel</b>")
        main_layout.addWidget(status_label)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Name", "Type", "Mock", "Status"])
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.device_table)
        
        # --- Connect / Disconnect Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect All")
        self.btn_disconnect = QPushButton("Disconnect All")
        
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        main_layout.addLayout(btn_layout)
        
        # --- Log Output Panel ---
        log_label = QLabel("<b>Log Output Panel</b>")
        main_layout.addWidget(log_label)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(self.log_text_edit)
        
        # Wiring up UI actions to DeviceManager
        self.btn_connect.clicked.connect(self.device_manager.connect_all)
        self.btn_disconnect.clicked.connect(self.device_manager.disconnect_all)
        
        # Listen to DeviceManager signals to update UI
        self.device_manager.device_status_changed.connect(self.update_device_status)

    def _populate_devices(self):
        """Populates the device table with initial configurations."""
        devices = self.device_manager.get_devices()
        self.device_table.setRowCount(len(devices))
        
        for row, (name, model) in enumerate(devices.items()):
            name_item = QTableWidgetItem(name)
            type_item = QTableWidgetItem(model.type.upper())
            mock_item = QTableWidgetItem("Yes" if model.mock else "No")
            status_item = QTableWidgetItem("Disconnected")
            
            # Center text and color status
            for item in (name_item, type_item, mock_item, status_item):
                item.setTextAlignment(Qt.AlignCenter)
                
            status_item.setForeground(QColor("red"))
                
            self.device_table.setItem(row, 0, name_item)
            self.device_table.setItem(row, 1, type_item)
            self.device_table.setItem(row, 2, mock_item)
            self.device_table.setItem(row, 3, status_item)

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        """Appends a new log message to the log panel."""
        color = "black"
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "DEBUG":
            color = "gray"
            
        html_msg = f'<span style="color:{color};">{message}</span><br>'
        self.log_text_edit.insertHtml(html_msg)
        
        # Scroll to bottom
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(str, bool)
    def update_device_status(self, device_name: str, is_connected: bool):
        """Updates the status column for a specific device."""
        for row in range(self.device_table.rowCount()):
            item = self.device_table.item(row, 0)
            if item and item.text() == device_name:
                status_item = self.device_table.item(row, 3)
                if is_connected:
                    status_item.setText("Connected")
                    status_item.setForeground(QColor("green"))
                else:
                    status_item.setText("Disconnected")
                    status_item.setForeground(QColor("red"))
                break

    def closeEvent(self, event):
        """Ensure threads are cleaned up when window closes."""
        self.device_manager.cleanup()
        super().closeEvent(event)
