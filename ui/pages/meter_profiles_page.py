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
            QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }
        """)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 20, 15, 20)

        title_label = QLabel("Meter Profiles")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #1E293B; border: none;")
        left_layout.addWidget(title_label)

        self.list_profiles = QListWidget()
        self.list_profiles.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; font-size: 14px; }
            QListWidget::item { padding: 14px; border-radius: 8px; margin-bottom: 6px; color: #475569; font-weight: 500; }
            QListWidget::item:hover { background-color: #F8FAFC; color: #1E293B; }
            QListWidget::item:selected { background-color: #EEF2FF; color: #4338CA; font-weight: bold; border-left: 4px solid #4F46E5; }
        """)
        self.list_profiles.itemSelectionChanged.connect(self._on_profile_selected)
        left_layout.addWidget(self.list_profiles)

        self.btn_new_profile = QPushButton("+ New Profile")
        self.btn_new_profile.setStyleSheet("""
            QPushButton { background-color: #4F46E5; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #4338CA; }
        """)
        self.btn_new_profile.clicked.connect(self._create_new_profile)
        left_layout.addWidget(self.btn_new_profile)

        # ---------------- Right Panel: Profile Editor ----------------
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }
            QLineEdit, QComboBox { padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; color: #1E293B; font-size: 14px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #818CF8; background: #FFFFFF; }
            QLabel { color: #475569; font-weight: 600; font-size: 13px; border: none; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                selection-background-color: #EEF2FF;
                selection-color: #4338CA;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 4px 8px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #CBD5E1;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(30, 30, 30, 30)

        self.editor_title = QLabel("Edit Profile")
        self.editor_title.setStyleSheet("color: #0F172A; font-size: 20px; font-weight: bold; border: none; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 10px;")
        right_layout.addWidget(self.editor_title)
        
        # We need a scroll area because the form is getting tall
        scroll_area = QScrollArea()
        scroll_area.setObjectName("profile_scroll_area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("#profile_scroll_area { background: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("profile_scroll_content")
        scroll_content.setStyleSheet("#profile_scroll_content { background: transparent; }")
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(15)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. L&T 3-Phase Meter")
        form_layout.addRow("Profile Name:", self.input_name)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Serial", "DLMS", "External"])
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)
        form_layout.addRow("Communication Mode:", self.combo_mode)

        # --- Dynamic DLMS Settings ---
        self.dlms_container = QWidget()
        dlms_layout = QFormLayout(self.dlms_container)
        dlms_layout.setContentsMargins(0, 0, 0, 0)
        self.input_client_addr = QLineEdit()
        self.input_server_addr = QLineEdit()
        self.input_auth = QComboBox()
        self.input_auth.addItems(["None", "Low", "High", "High_MD5", "High_SHA1", "High_GMAC", "High_SHA256"])
        self.input_password = QLineEdit()
        self.input_system_title = QLineEdit()
        self.input_auth_key = QLineEdit()
        self.input_block_cipher_key = QLineEdit()
        dlms_layout.addRow("Client Address:", self.input_client_addr)
        dlms_layout.addRow("Server Address:", self.input_server_addr)
        dlms_layout.addRow("Authentication:", self.input_auth)
        dlms_layout.addRow("Password:", self.input_password)
        dlms_layout.addRow("System Title (Hex):", self.input_system_title)
        dlms_layout.addRow("Auth Key (Hex):", self.input_auth_key)
        dlms_layout.addRow("Block Cipher Key (Hex):", self.input_block_cipher_key)
        form_layout.addRow(self.dlms_container)
        
        # --- Dynamic Serial Settings ---
        self.serial_container = QWidget()
        serial_layout = QFormLayout(self.serial_container)
        serial_layout.setContentsMargins(0, 0, 0, 0)
        self.input_baudrate = QComboBox()
        self.input_baudrate.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.input_timeout = QLineEdit()
        self.combo_write_term = QComboBox()
        self.combo_write_term.addItems(["\\r\\n (CRLF)", "\\r (CR)", "\\n (LF)", "None"])
        serial_layout.addRow("Baudrate:", self.input_baudrate)
        serial_layout.addRow("Timeout (s):", self.input_timeout)
        serial_layout.addRow("Write Terminator:", self.combo_write_term)
        form_layout.addRow(self.serial_container)

        # Commands Section
        self.cmds_container = QWidget()
        cmds_layout = QFormLayout(self.cmds_container)
        cmds_layout.setContentsMargins(0, 0, 0, 0)
        
        cmds_label = QLabel("Command Mappings")
        cmds_label.setStyleSheet("color: #1E293B; font-size: 16px; font-weight: bold; border: none; border-bottom: 1px solid #E2E8F0; padding-top: 15px; padding-bottom: 8px; margin-bottom: 5px;")
        cmds_layout.addRow(cmds_label)

        # Helpers for creating command rows
        self.cmd_inputs = {}
        
        def add_command_row(key, label_text):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            val_input = QLineEdit()
            
            val_fmt_btn = QPushButton("HEX")
            val_fmt_btn.setFixedWidth(60)
            val_fmt_btn.setCursor(Qt.PointingHandCursor)
            val_fmt_btn.setStyleSheet("QPushButton { background-color: #E2E8F0; color: #1E293B; border-radius: 4px; font-weight: bold; padding: 8px; } QPushButton:hover { background-color: #CBD5E1; }")
            val_fmt_btn.clicked.connect(lambda _, b=val_fmt_btn: b.setText("ASCII" if b.text() == "HEX" else "HEX"))
            
            resp_input = QLineEdit()
            
            term_input = QLineEdit()
            term_input.setFixedWidth(100)
            
            row_layout.addWidget(val_input, stretch=2)
            row_layout.addWidget(val_fmt_btn)
            row_layout.addWidget(resp_input, stretch=2)
            row_layout.addWidget(term_input, stretch=1)
            
            lbl = QLabel(f"{label_text}:")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            cmds_layout.addRow(lbl, row_layout)
            self.cmd_inputs[key] = {
                "val_input": val_input, 
                "val_fmt_btn": val_fmt_btn, 
                "resp_input": resp_input, 
                "term_input": term_input
            }

        add_command_row("read_serial_number", "Read Serial Number")
        add_command_row("unlock", "Unlock Command")
        add_command_row("close_load_switch", "Close Load Switch")
        add_command_row("open_load_switch", "Open Load Switch")
        
        form_layout.addRow(self.cmds_container)

        scroll_area.setWidget(scroll_content)
        right_layout.addWidget(scroll_area)

        # Action Buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("QPushButton { background-color: #EF4444; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #DC2626; }")
        self.btn_delete.clicked.connect(self._delete_profile)
        actions_layout.addWidget(self.btn_delete)
        
        self.btn_save = QPushButton("Save Profile")
        self.btn_save.setStyleSheet("QPushButton { background-color: #10B981; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #059669; }")
        self.btn_save.clicked.connect(self._save_profile)
        actions_layout.addWidget(self.btn_save)

        right_layout.addLayout(actions_layout)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        
        self._set_editor_enabled(False)
        self._on_mode_changed(self.combo_mode.currentText())

    def _on_mode_changed(self, mode):
        is_dlms = (mode == "DLMS")
        is_serial = (mode == "Serial")
        is_external = (mode == "External")
        
        self.dlms_container.setVisible(is_dlms)
        self.serial_container.setVisible(is_serial)
        self.cmds_container.setVisible(not is_external)
        
        for key, inputs in self.cmd_inputs.items():
            inputs["val_fmt_btn"].setVisible(is_serial)
            inputs["term_input"].setVisible(is_serial)
            
            if is_dlms:
                inputs["val_input"].setPlaceholderText("OBIS Code (e.g. 1.0.0.0.0.255)")
                inputs["resp_input"].setPlaceholderText("Expected response (optional)")
            elif is_serial:
                inputs["val_input"].setPlaceholderText("Command payload...")
                inputs["resp_input"].setPlaceholderText("Expected response (HEX/ASCII)")
                inputs["term_input"].setPlaceholderText("Terminator")

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
            self.input_client_addr.clear()
            self.input_server_addr.clear()
            self.input_password.clear()
            self.input_system_title.clear()
            self.input_auth_key.clear()
            self.input_block_cipher_key.clear()
            self.input_timeout.clear()
            self.combo_write_term.setCurrentIndex(0)
            
            for key, inputs in self.cmd_inputs.items():
                inputs["val_input"].clear()
                inputs["val_fmt_btn"].setText("HEX")
                inputs["resp_input"].clear()
                inputs["term_input"].clear()
            self.current_profile_id = None
            self.editor_title.setText("Select or create a profile")

    def _create_new_profile(self):
        self.list_profiles.clearSelection()
        self.current_profile_id = None
        self._set_editor_enabled(True)
        self.editor_title.setText("New Profile")
        self.btn_delete.setEnabled(False)
        
        self.input_name.clear()
        self.combo_mode.setCurrentText("External")
        self.input_client_addr.setText("48")
        self.input_server_addr.setText("1")
        self.input_auth.setCurrentText("High")
        self.input_password.clear()
        self.input_system_title.clear()
        self.input_auth_key.clear()
        self.input_block_cipher_key.clear()
        self.input_baudrate.setCurrentText("9600")
        self.input_timeout.setText("2.0")
        self.combo_write_term.setCurrentIndex(0)
        
        for key, inputs in self.cmd_inputs.items():
            inputs["val_input"].clear()
            inputs["val_fmt_btn"].setText("HEX")
            inputs["resp_input"].clear()
            inputs["term_input"].clear()

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
        self.combo_mode.setCurrentText(profile.get("communication_mode", "External"))
        
        dlms = profile.get("dlms_settings", {})
        self.input_client_addr.setText(str(dlms.get("client_address", "48")))
        self.input_server_addr.setText(str(dlms.get("server_address", "1")))
        self.input_auth.setCurrentText(dlms.get("authentication", "High"))
        self.input_password.setText(dlms.get("password", ""))
        self.input_system_title.setText(dlms.get("system_title", ""))
        self.input_auth_key.setText(dlms.get("authentication_key", ""))
        self.input_block_cipher_key.setText(dlms.get("block_cipher_key", ""))
        
        serial = profile.get("serial_settings", {})
        self.input_baudrate.setCurrentText(str(serial.get("baudrate", "9600")))
        self.input_timeout.setText(str(serial.get("timeout", "2.0")))
        write_term = serial.get("write_terminator", "\\r\\n")
        term_map = {
            "\\r\\n": "\\r\\n (CRLF)",
            "\\r": "\\r (CR)",
            "\\n": "\\n (LF)",
            "None": "None"
        }
        self.combo_write_term.setCurrentText(term_map.get(write_term, "\\r\\n (CRLF)"))
        
        cmds = profile.get("commands", {})
        for key, inputs in self.cmd_inputs.items():
            cmd_data = cmds.get(key, {})
            inputs["val_input"].setText(cmd_data.get("value", ""))
            inputs["val_fmt_btn"].setText(cmd_data.get("format", "HEX").upper())
            inputs["resp_input"].setText(cmd_data.get("expected_response", ""))
            inputs["term_input"].setText(cmd_data.get("expected_terminator", ""))

    def _save_profile(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            return

        profile_data = {
            "id": self.current_profile_id,
            "name": name,
            "communication_mode": self.combo_mode.currentText(),
            "dlms_settings": {
                "client_address": int(self.input_client_addr.text() or 48),
                "server_address": int(self.input_server_addr.text() or 1),
                "authentication": self.input_auth.currentText(),
                "password": self.input_password.text().strip(),
                "system_title": self.input_system_title.text().strip(),
                "authentication_key": self.input_auth_key.text().strip(),
                "block_cipher_key": self.input_block_cipher_key.text().strip()
            },
            "serial_settings": {
                "baudrate": int(self.input_baudrate.currentText() or 9600),
                "timeout": float(self.input_timeout.text() or 2.0),
                "write_terminator": self.combo_write_term.currentText().split(" ")[0]
            },
            "commands": {}
        }
        
        for key, inputs in self.cmd_inputs.items():
            profile_data["commands"][key] = {
                "value": inputs["val_input"].text().strip(),
                "format": inputs["val_fmt_btn"].text(),
                "expected_response": inputs["resp_input"].text().strip(),
                "expected_terminator": inputs["term_input"].text().strip()
            }

        success = self.profile_manager.save_profile(profile_data)
        if success:
            self.main_window.append_log("INFO", f"Saved meter profile: {name}")
            self._load_profiles_list()
            
            for i in range(self.list_profiles.count()):
                item = self.list_profiles.item(i)
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
