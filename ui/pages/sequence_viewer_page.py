import os
import importlib
import inspect
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QLabel, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SequenceViewerPage(QWidget):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.device_manager = device_manager
        self.main_window = main_window
        self.discovered_tests = {}
        
        self._setup_ui()
        self._populate_tests()
        
    def _setup_ui(self):
        # Main Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Left Panel - Test List
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(300)
        self.left_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        
        title_label = QLabel("Available Tests")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #1E293B; border: none;")
        left_layout.addWidget(title_label)
        
        self.list_tests = QListWidget()
        self.list_tests.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 4px;
                color: #334155;
            }
            QListWidget::item:hover {
                background-color: #F1F5F9;
            }
            QListWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
                font-weight: bold;
            }
        """)
        self.list_tests.itemSelectionChanged.connect(self._on_test_selected)
        left_layout.addWidget(self.list_tests)
        
        # Right Panel - Sequence Timeline
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        
        self.sequence_title = QLabel("Select a test to view its sequence")
        self.sequence_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.sequence_title.setStyleSheet("color: #0F172A; border: none; padding-bottom: 10px;")
        right_layout.addWidget(self.sequence_title)
        
        # Scroll Area for steps
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.steps_layout = QVBoxLayout(self.scroll_content)
        self.steps_layout.setAlignment(Qt.AlignTop)
        self.steps_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.scroll_content)
        right_layout.addWidget(self.scroll_area)
        
        # Add to main layout
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)

    def _populate_tests(self):
        from core.test_definitions.base_test import BaseTest
        test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "test_definitions")
        
        if not os.path.exists(test_dir): return
            
        for file in os.listdir(test_dir):
            if file.endswith(".py") and file not in ["__init__.py", "base_test.py"]:
                module_name = f"core.test_definitions.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseTest) and obj is not BaseTest:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name.replace("Test", ""))
                            self.discovered_tests[name] = obj
                            self.list_tests.addItem(display_name)
                            self.list_tests.item(self.list_tests.count()-1).setData(Qt.UserRole, name)
                except Exception as e:
                    self.main_window.append_log("ERROR", f"Failed to load test {file}: {e}")
                    
        if self.list_tests.count() > 0:
            self.list_tests.setCurrentRow(0)

    def _on_test_selected(self):
        selected = self.list_tests.selectedItems()
        if not selected: return
        
        test_name = selected[0].text()
        test_class_name = selected[0].data(Qt.UserRole)
        test_class = self.discovered_tests.get(test_class_name)
        
        if not test_class: return
        
        self.sequence_title.setText(f"{test_name} Sequence")
        
        # Clear existing steps
        while self.steps_layout.count():
            child = self.steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Instantiate test to get builder steps
        try:
            test_instance = test_class()
            steps = test_instance.get_steps()
            
            for i, step in enumerate(steps):
                self._add_step_card(str(i + 1), step, self.steps_layout)
        except Exception as e:
            err = QLabel(f"Error loading test steps: {str(e)}")
            self.steps_layout.addWidget(err)

    def _add_step_card(self, prefix, step, parent_layout):
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-radius: 6px;
                border: 1px solid #E2E8F0;
                padding: 4px;
            }
            QFrame:hover {
                border-color: #94A3B8;
                background-color: #F1F5F9;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        
        # Index Badge
        idx_badge = QLabel(prefix)
        idx_badge.setFixedSize(30, 30)
        idx_badge.setAlignment(Qt.AlignCenter)
        idx_badge.setFont(QFont("Segoe UI", 12, QFont.Bold))
        idx_badge.setStyleSheet("""
            QLabel {
                background-color: #E0E7FF;
                color: #4F46E5;
                border-radius: 15px;
                border: none;
            }
        """)
        layout.addWidget(idx_badge)
        
        # Step Content
        content_layout = QVBoxLayout()
        
        name_lbl = QLabel(step.name)
        name_lbl.setFont(QFont("Segoe UI", 14, QFont.Medium))
        name_lbl.setStyleSheet("color: #1E293B; border: none; background: transparent;")
        content_layout.addWidget(name_lbl)
        
        if hasattr(step, 'details') and step.details:
            details_lbl = QLabel(step.details)
            details_lbl.setWordWrap(True)
            details_lbl.setStyleSheet("color: #475569; font-size: 13px; font-style: italic; border: none; background: transparent;")
            content_layout.addWidget(details_lbl)
        
        # Metadata row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(15)
        

        if step.requires_input:
            inp_lbl = QLabel("⌨ Requires User Input")
            inp_lbl.setStyleSheet("color: #D97706; font-size: 11px; font-weight: bold; border: none; background: transparent;")
            meta_layout.addWidget(inp_lbl)
            
        if hasattr(step, 'device') and step.device:
            dev_lbl = QLabel(f"🔌 {step.device}")
            dev_lbl.setStyleSheet("color: #059669; font-size: 11px; font-weight: bold; border: none; background: transparent; padding: 2px 6px; border-radius: 4px; background-color: #D1FAE5;")
            meta_layout.addWidget(dev_lbl)
            
        meta_layout.addStretch()
        content_layout.addLayout(meta_layout)
        
        layout.addLayout(content_layout)
        layout.setStretch(1, 1)
        
        parent_layout.addWidget(card)
        
        # Render nested steps if any
        if getattr(step, 'sub_steps', None):
            sub_container = QFrame()
            sub_container.setStyleSheet("background: transparent; border-left: 3px solid #CBD5E1; margin-left: 20px;")
            sub_layout = QVBoxLayout(sub_container)
            sub_layout.setContentsMargins(15, 5, 0, 10)
            sub_layout.setSpacing(8)
            
            for j, sub_step in enumerate(step.sub_steps):
                self._add_step_card(f"{prefix}.{j+1}", sub_step, sub_layout)
                
            parent_layout.addWidget(sub_container)
