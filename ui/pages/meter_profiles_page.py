from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QLabel, QFrame, QLineEdit, QComboBox, QPushButton,
    QFormLayout, QMessageBox, QGraphicsDropShadowEffect,
    QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from services.profile_manager import ProfileManager

class MeterProfilesPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.profile_manager = ProfileManager()
        self.current_profile_id = None
        
        self._setup_ui()
        self._load_profiles_list()

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(300)
        self.left_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)
        shadow1 = QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(15)
        shadow1.setColor(QColor(0, 0, 0, 15))
        shadow1.setOffset(0, 4)
        self.left_panel.setGraphicsEffect(shadow1)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 20, 15, 20)

        title_label = QLabel("Meter Profiles")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #1E293B; border: none;")
        left_layout.addWidget(title_label)

        self.list_profiles = QListWidget()
        self.list_profiles.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 14px;
                border-radius: 8px;
                margin-bottom: 6px;
                color: #475569;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #F8FAFC;
                color: #1E293B;
            }
            QListWidget::item:selected {
                background-color: #EEF2FF;
                color: #4338CA;
                font-weight: bold;
                border-left: 4px solid #4F46E5;
            }
        """)
        self.list_profiles.itemSelectionChanged.connect(self._on_profile_selected)
        left_layout.addWidget(self.list_profiles)

        self.btn_new_profile = QPushButton("+ New Profile")
        self.btn_new_profile.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        self.btn_new_profile.clicked.connect(self._create_new_profile)
        left_layout.addWidget(self.btn_new_profile)

        # ---------------- Right Panel: Profile Editor ----------------
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: #F8FAFC;
                color: #1E293B;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #818CF8;
                background: #FFFFFF;
            }
            QLabel {
                color: #475569;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }
        """)
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 15))
        shadow2.setOffset(0, 4)
        self.right_panel.setGraphicsEffect(shadow2)

        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(30, 30, 30, 30)

        self.editor_title = QLabel("Edit Profile")
        self.editor_title.setStyleSheet("""
            color: #0F172A; 
            font-size: 20px; 
            font-weight: bold; 
            border: none; 
            border-bottom: 2px solid #E2E8F0; 
            padding-bottom: 8px; 
            margin-bottom: 10px;
        """)
        right_layout.addWidget(self.editor_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. L&T 3-Phase Meter")
        form_layout.addRow("Profile Name:", self.input_name)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Serial", "DLMS"])
        form_layout.addRow("Communication Mode:", self.combo_mode)

        # Commands Section
        cmds_label = QLabel("Command Mappings")
        cmds_label.setStyleSheet("""
            color: #1E293B; 
            font-size: 16px; 
            font-weight: bold; 
            border: none; 
            border-bottom: 1px solid #E2E8F0; 
            padding-top: 15px; 
            padding-bottom: 8px; 
            margin-bottom: 5px;
        """)
        form_layout.addRow(cmds_label)

        # Helpers for creating command rows
        self.cmd_inputs = {}
        
        def add_command_row(key, label_text):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            val_input = QLineEdit()
            val_input.setPlaceholderText(f"Command...")
            
            val_fmt_btn = QPushButton("HEX")
            val_fmt_btn.setFixedWidth(60)
            val_fmt_btn.setCursor(Qt.PointingHandCursor)
            val_fmt_btn.setStyleSheet("QPushButton { background-color: #E2E8F0; color: #1E293B; border-radius: 4px; font-weight: bold; padding: 8px; } QPushButton:hover { background-color: #CBD5E1; }")
            val_fmt_btn.clicked.connect(lambda _, b=val_fmt_btn: b.setText("ASCII" if b.text() == "HEX" else "HEX"))
            
            term_input = QLineEdit()
            term_input.setPlaceholderText("Terminator...")
            term_input.setFixedWidth(120)
            
            term_fmt_btn = QPushButton("HEX")
            term_fmt_btn.setFixedWidth(60)
            term_fmt_btn.setCursor(Qt.PointingHandCursor)
            term_fmt_btn.setStyleSheet("QPushButton { background-color: #E2E8F0; color: #1E293B; border-radius: 4px; font-weight: bold; padding: 8px; } QPushButton:hover { background-color: #CBD5E1; }")
            term_fmt_btn.clicked.connect(lambda _, b=term_fmt_btn: b.setText("ASCII" if b.text() == "HEX" else "HEX"))
            
            row_layout.addWidget(val_input, stretch=1)
            row_layout.addWidget(val_fmt_btn)
            row_layout.addWidget(term_input)
            row_layout.addWidget(term_fmt_btn)
            
            lbl = QLabel(f"{label_text}:")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            form_layout.addRow(lbl, row_layout)
            self.cmd_inputs[key] = (val_input, val_fmt_btn, term_input, term_fmt_btn)

        add_command_row("read_serial_number", "Read Serial Number")
        add_command_row("close_load_switch", "Close Load Switch")
        add_command_row("open_load_switch", "Open Load Switch")

        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        # Action Buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.btn_delete.clicked.connect(self._delete_profile)
        actions_layout.addWidget(self.btn_delete)
        
        self.btn_save = QPushButton("Save Profile")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_save.clicked.connect(self._save_profile)
        actions_layout.addWidget(self.btn_save)

        right_layout.addLayout(actions_layout)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        
        self._set_editor_enabled(False)

    def _load_profiles_list(self):
        self.list_profiles.blockSignals(True)
        self.list_profiles.clear()
        profiles = self.profile_manager.get_all_profiles()
        for p in profiles:
            self.list_profiles.addItem(p.get("name", "Unnamed Profile"))
            self.list_profiles.item(self.list_profiles.count()-1).setData(Qt.UserRole, p.get("id"))
        self.list_profiles.blockSignals(False)

    def _set_editor_enabled(self, enabled):
        self.right_panel.setEnabled(enabled)
        if not enabled:
            self.input_name.clear()
            for key, (val_input, val_fmt_btn, term_input, term_fmt_btn) in self.cmd_inputs.items():
                val_input.clear()
                val_fmt_btn.setText("HEX")
                term_input.clear()
                term_fmt_btn.setText("HEX")
            self.current_profile_id = None
            self.editor_title.setText("Select or create a profile")

    def _create_new_profile(self):
        self.list_profiles.clearSelection()
        self.current_profile_id = None
        self.input_name.clear()
        self.combo_mode.setCurrentText("DLMS")
        for key, (val_input, val_fmt_btn, term_input, term_fmt_btn) in self.cmd_inputs.items():
            val_input.clear()
            val_fmt_btn.setText("HEX")
            term_input.clear()
            term_fmt_btn.setText("HEX")
            
        self.editor_title.setText("New Profile")
        self._set_editor_enabled(True)
        self.btn_delete.setEnabled(False)

    def _on_profile_selected(self):
        selected = self.list_profiles.selectedItems()
        if not selected:
            self._set_editor_enabled(False)
            return
            
        profile_id = selected[0].data(Qt.UserRole)
        profile = self.profile_manager.get_profile(profile_id)
        if not profile: return

        self.current_profile_id = profile_id
        self.editor_title.setText("Edit Profile")
        self._set_editor_enabled(True)
        self.btn_delete.setEnabled(True)

        self.input_name.setText(profile.get("name", ""))
        self.combo_mode.setCurrentText(profile.get("communication_mode", "DLMS"))
        
        cmds = profile.get("commands", {})
        for key, (val_input, val_fmt_btn, term_input, term_fmt_btn) in self.cmd_inputs.items():
            cmd_data = cmds.get(key, {})
            val_input.setText(cmd_data.get("value", ""))
            val_fmt_btn.setText(cmd_data.get("format", "HEX").upper())
            term_input.setText(cmd_data.get("terminator", ""))
            term_fmt_btn.setText(cmd_data.get("terminator_format", "HEX").upper())

    def _save_profile(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            return

        profile_data = {
            "id": self.current_profile_id,
            "name": name,
            "communication_mode": self.combo_mode.currentText(),
            "commands": {}
        }
        
        for key, (val_input, val_fmt_btn, term_input, term_fmt_btn) in self.cmd_inputs.items():
            profile_data["commands"][key] = {
                "value": val_input.text().strip(),
                "format": val_fmt_btn.text(),
                "terminator": term_input.text().strip(),
                "terminator_format": term_fmt_btn.text()
            }

        success = self.profile_manager.save_profile(profile_data)
        if success:
            self.main_window.append_log("INFO", f"Saved meter profile: {name}")
            self._load_profiles_list()
            
            # Select the newly saved or updated item
            for i in range(self.list_profiles.count()):
                item = self.list_profiles.item(i)
                # If it's a new profile, we need to match by name (since ID was None before save)
                if self.current_profile_id:
                    if item.data(Qt.UserRole) == self.current_profile_id:
                        item.setSelected(True)
                        break
                else:
                    if item.text() == name:
                        item.setSelected(True)
                        break
        else:
            QMessageBox.critical(self, "Error", "Failed to save profile.")

    def _delete_profile(self):
        if not self.current_profile_id: return
        
        reply = QMessageBox.question(self, 'Delete Profile', 'Are you sure you want to delete this profile?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.profile_manager.delete_profile(self.current_profile_id):
                self.main_window.append_log("INFO", "Deleted meter profile.")
                self._load_profiles_list()
                self._set_editor_enabled(False)
            else:
                QMessageBox.critical(self, "Error", "Failed to delete profile.")
