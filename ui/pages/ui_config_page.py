from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtGui import (QFont, QIcon)
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QVBoxLayout, QWidget, QAbstractItemView, QHeaderView, QTextEdit)

class Ui_ConfigPage(object):
    def setupUi(self, ConfigPage):
        if not ConfigPage.objectName():
            ConfigPage.setObjectName(u"ConfigPage")
        
        self.main_layout = QHBoxLayout(ConfigPage)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Sidebar: Test Suite List & Palette ---
        self.sidebar_container = QFrame(ConfigPage)
        self.sidebar_container.setObjectName(u"sidebar_container")
        self.sidebar_container.setMinimumWidth(280)
        self.sidebar_container.setMaximumWidth(320)
        self.sidebar_container.setFrameShape(QFrame.StyledPanel)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setSpacing(15)
        self.sidebar_layout.setContentsMargins(10, 15, 10, 15)
        
        # Saved Suites Section
        self.suites_section = QVBoxLayout()
        self.suites_section.setSpacing(5)
        self.lbl_suites_title = QLabel("Test Suites")
        self.lbl_suites_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #64748B; text-transform: uppercase;")
        self.suites_section.addWidget(self.lbl_suites_title)
        
        self.list_suites = QListWidget(self.sidebar_container)
        self.list_suites.setObjectName(u"list_suites")
        self.list_suites.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.suites_section.addWidget(self.list_suites)
        
        self.btn_new_suite = QPushButton("Create New Suite")
        self.btn_new_suite.setObjectName(u"btn_new_suite")
        self.btn_new_suite.setMinimumHeight(35)
        self.suites_section.addWidget(self.btn_new_suite)
        self.sidebar_layout.addLayout(self.suites_section)
        
        # Separator Line
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setStyleSheet("color: #E2E8F0; margin: 5px 0px;")
        self.sidebar_layout.addWidget(self.line)
        
        # Step Palette Section
        self.palette_section = QVBoxLayout()
        self.palette_section.setSpacing(5)
        self.lbl_palette_title = QLabel("Available Steps")
        self.lbl_palette_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #64748B; text-transform: uppercase;")
        self.palette_section.addWidget(self.lbl_palette_title)
        
        self.lbl_palette_hint = QLabel("Drag steps into the sequence")
        self.lbl_palette_hint.setStyleSheet("font-size: 11px; color: #94A3B8; margin-bottom: 2px;")
        self.palette_section.addWidget(self.lbl_palette_hint)
        
        self.list_palette = QListWidget(ConfigPage)
        self.list_palette.setObjectName(u"list_palette")
        self.list_palette.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.palette_section.addWidget(self.list_palette)
        self.sidebar_layout.addLayout(self.palette_section)
        
        self.main_layout.addWidget(self.sidebar_container)
        
        # --- Main Content: Step Editor ---
        self.editor_container = QFrame(ConfigPage)
        self.editor_container.setObjectName(u"editor_container")
        self.editor_container.setFrameShape(QFrame.StyledPanel)
        
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setSpacing(10)
        self.editor_layout.setContentsMargins(20, 20, 20, 20)
        
        # Suite Metadata
        self.meta_layout = QHBoxLayout()
        self.meta_layout.setSpacing(10)
        self.lbl_suite_name = QLabel("Suite Name:")
        self.input_suite_name = QLineEdit()
        self.input_suite_name.setPlaceholderText("Enter suite name...")
        self.meta_layout.addWidget(self.lbl_suite_name)
        self.meta_layout.addWidget(self.input_suite_name)
        self.editor_layout.addLayout(self.meta_layout)
        
        self.input_suite_desc = QTextEdit()
        self.input_suite_desc.setPlaceholderText("Enter suite description...")
        self.input_suite_desc.setMaximumHeight(60)
        self.editor_layout.addWidget(self.input_suite_desc)
        
        # Steps Sequence Header
        self.header_layout = QHBoxLayout()
        self.lbl_steps_title = QLabel("Test Sequence")
        self.lbl_steps_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1E293B;")
        self.header_layout.addWidget(self.lbl_steps_title)
        self.header_layout.addStretch()
        
        self.btn_add_step = QPushButton("+ Add Step")
        self.btn_add_step.setObjectName(u"btn_add_step")
        self.header_layout.addWidget(self.btn_add_step)
        self.editor_layout.addLayout(self.header_layout)
        
        # Replace Table with ListWidget for better drag & drop cards
        self.list_steps_sequence = QListWidget()
        self.list_steps_sequence.setObjectName(u"list_steps_sequence")
        self.list_steps_sequence.setSpacing(8)
        self.list_steps_sequence.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_steps_sequence.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_steps_sequence.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor_layout.addWidget(self.list_steps_sequence)
        
        # Action Buttons
        self.actions_layout = QHBoxLayout()
        
        self.btn_save_suite = QPushButton("Save Test Suite")
        self.btn_save_suite.setObjectName(u"btn_save_suite")
        self.btn_save_suite.setMinimumWidth(150)
        self.btn_save_suite.setMinimumHeight(40)
        self.btn_save_suite.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; border-radius: 8px;")
        
        self.btn_delete_suite = QPushButton("Delete Suite")
        self.btn_delete_suite.setObjectName(u"btn_delete_suite")
        self.btn_delete_suite.setMinimumHeight(40)
        self.btn_delete_suite.setStyleSheet("background-color: #EF4444; color: white; border-radius: 8px;")
        
        self.actions_layout.addStretch()
        self.actions_layout.addWidget(self.btn_delete_suite)
        self.actions_layout.addWidget(self.btn_save_suite)
        self.editor_layout.addLayout(self.actions_layout)
        
        self.main_layout.addWidget(self.editor_container)
        
        self.retranslateUi(ConfigPage)
        QMetaObject.connectSlotsByName(ConfigPage)

    def retranslateUi(self, ConfigPage):
        ConfigPage.setWindowTitle(QCoreApplication.translate("ConfigPage", u"Test Configuration", None))
