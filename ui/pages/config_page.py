from PySide6.QtWidgets import (QWidget, QTableWidgetItem, QHeaderView, QPushButton, 
                             QHBoxLayout, QDialog, QVBoxLayout, QComboBox, QFormLayout, 
                             QLineEdit, QDoubleSpinBox, QSpinBox, QMessageBox, QLabel,
                             QListWidget, QListWidgetItem, QAbstractItemView, QFrame, QSizePolicy)
from PySide6.QtCore import Slot, Qt, QMimeData, QPoint, Signal
from PySide6.QtGui import QDrag, QPainter, QColor, QPen, QIcon, QFont
from ui.pages.ui_config_page import Ui_ConfigPage
from models.test_suite_model import TestSuiteModel, TestStepConfig
import json


class StepRegistry:
    _steps = {
        "SET_SOURCE": {"desc": "Set Voltage/Current", "params": {"voltage": (float, 240.0), "current": (float, 5.0), "pf": (float, 1.0)}},
        "TURN_LOAD": {"desc": "Toggle Load ON/OFF", "params": {"state": (bool, True)}},
        "WAIT": {"desc": "Delay Execution", "params": {"duration_sec": (float, 5.0)}},
        "READ_METER": {"desc": "Read DLMS/Modbus", "params": {"registers": (str, "")}},
        "READ_MFM_METER": {"desc": "Read MFM Meter", "params": {"registers": (str, "10, 11")}},
        "PROMPT_USER": {"desc": "User Interaction", "params": {"message": (str, ""), "requires_input": (bool, False)}},
        "WAIT_UNTIL_ZERO": {"desc": "Wait for Current Drop", "params": {"threshold": (float, 0.1), "timeout_sec": (int, 30)}},
        "REPEAT": {"desc": "Loop Sequence", "params": {"start_step": (int, 1), "end_step": (int, 1), "iterations": (int, 3)}}
    }
    
    @classmethod
    def get_all_types(cls):
        return list(cls._steps.keys())
        
    @classmethod
    def get_description(cls, stype):
        return cls._steps.get(stype, {}).get("desc", stype)
        
    @classmethod
    def get_default_params(cls, stype):
        defaults = {}
        for k, (t, v) in cls._steps.get(stype, {}).get("params", {}).items():
            defaults[k] = v
        return defaults

class StepEditDialog(QDialog):
    """Dialog to add or edit a test step."""
    def __init__(self, parent=None, step_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Test Step")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QLabel {
                color: #334155;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px;
                color: #0F172A;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none; /* Custom arrow could be added here */
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748B;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                selection-background-color: #3B82F6;
                selection-color: white;
                color: #1E293B;
                outline: none;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
        """)
        self.layout = QVBoxLayout(self)
        
        self.form = QFormLayout()
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(StepRegistry.get_all_types())
        self.form.addRow("Step Type:", self.combo_type)
        
        # Dynamic parameter container
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.param_container)
        
        self.inputs = {}
        
        self.combo_type.currentTextChanged.connect(self._update_params)
        
        # Action Buttons
        self.buttons = QHBoxLayout()
        self.btn_ok = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.buttons.addWidget(self.btn_cancel)
        self.buttons.addWidget(self.btn_ok)
        self.layout.addLayout(self.buttons)
        
        if step_data:
            self.combo_type.setCurrentText(step_data.get('step_type', 'SET_SOURCE'))
            self._update_params()
            self._set_param_values(step_data.get('parameters', {}))
        else:
            self._update_params()

    def _update_params(self):
        # Clear previous inputs
        for i in reversed(range(self.param_layout.count())):
            item = self.param_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        self.inputs = {}
        
        stype = self.combo_type.currentText()
        if stype == "SET_SOURCE":
            v_input = QDoubleSpinBox(); v_input.setRange(0, 500); v_input.setValue(240.0)
            i_input = QDoubleSpinBox(); i_input.setRange(0, 100); i_input.setValue(5.0)
            pf_input = QDoubleSpinBox(); pf_input.setRange(-1, 1); pf_input.setValue(1.0)
            self.param_layout.addRow("Voltage (V):", v_input)
            self.param_layout.addRow("Current (A):", i_input)
            self.param_layout.addRow("Power Factor:", pf_input)
            self.inputs = {"voltage": v_input, "current": i_input, "pf": pf_input}
            
        elif stype == "TURN_LOAD":
            state_input = QComboBox(); state_input.addItems(["ON", "OFF"])
            self.param_layout.addRow("Load State:", state_input)
            self.inputs = {"state": state_input}
            
        elif stype == "WAIT":
            dur_input = QDoubleSpinBox(); dur_input.setRange(0.1, 3600); dur_input.setValue(5.0)
            self.param_layout.addRow("Duration (sec):", dur_input)
            self.inputs = {"duration_sec": dur_input}
            
        elif stype == "READ_METER":
            reg_input = QLineEdit(); reg_input.setPlaceholderText("Active Energy, Current Credit")
            self.param_layout.addRow("Registers (comma separated):", reg_input)
            self.inputs = {"registers": reg_input}
            
        elif stype == "READ_MFM_METER":
            reg_input = QLineEdit(); reg_input.setPlaceholderText("10, 11")
            self.param_layout.addRow("Registers (comma separated):", reg_input)
            self.inputs = {"registers": reg_input}
            
        elif stype == "PROMPT_USER":
            msg_input = QLineEdit(); msg_input.setPlaceholderText("Instruction for user...")
            req_input = QComboBox(); req_input.addItems(["NO", "YES"])
            self.param_layout.addRow("Message:", msg_input)
            self.param_layout.addRow("Requires Input?", req_input)
            self.inputs = {"message": msg_input, "requires_input": req_input}
            
        elif stype == "WAIT_UNTIL_ZERO":
            thresh = QDoubleSpinBox(); thresh.setRange(0, 10); thresh.setValue(0.1)
            timeout = QSpinBox(); timeout.setRange(1, 300); timeout.setValue(30)
            self.param_layout.addRow("Threshold (A):", thresh)
            self.param_layout.addRow("Timeout (sec):", timeout)
            self.inputs = {"threshold": thresh, "timeout_sec": timeout}
            
        elif stype == "REPEAT":
            start_input = QSpinBox(); start_input.setRange(1, 100); start_input.setValue(1)
            end_input = QSpinBox(); end_input.setRange(1, 100); end_input.setValue(1)
            count_input = QSpinBox(); count_input.setRange(2, 1000); count_input.setValue(3)
            self.param_layout.addRow("Start Step #:", start_input)
            self.param_layout.addRow("End Step #:", end_input)
            self.param_layout.addRow("Iterations:", count_input)
            self.inputs = {"start_step": start_input, "end_step": end_input, "iterations": count_input}

    def _set_param_values(self, params):
        for key, widget in self.inputs.items():
            if key in params:
                val = params[key]
                if isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                    widget.setValue(float(val))
                elif isinstance(widget, QComboBox):
                    if key == "state":
                        widget.setCurrentText("ON" if val else "OFF")
                    elif key == "requires_input":
                        widget.setCurrentText("YES" if val else "NO")
                    else:
                        widget.setCurrentText(str(val))
                elif isinstance(widget, QLineEdit):
                    if key == "registers" and isinstance(val, list):
                        widget.setText(", ".join(val))
                    else:
                        widget.setText(str(val))

    def get_data(self):
        data = {
            "step_type": self.combo_type.currentText(),
            "parameters": {}
        }
        for key, widget in self.inputs.items():
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                data["parameters"][key] = widget.value()
            elif isinstance(widget, QComboBox):
                if key == "state":
                    data["parameters"][key] = (widget.currentText() == "ON")
                elif key == "requires_input":
                    data["parameters"][key] = (widget.currentText() == "YES")
                else:
                    data["parameters"][key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                if key == "registers":
                    data["parameters"][key] = [r.strip() for r in widget.text().split(",") if r.strip()]
                else:
                    data["parameters"][key] = widget.text()
        return data

class StepCardWidget(QFrame):
    """Rich card-style widget for a test step in the sequence."""
    edit_clicked = Signal()
    delete_clicked = Signal()
    
    def __init__(self, index, step_type, params_summary, is_looping=False, loop_color=None):
        super().__init__()
        self.setObjectName("step_card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(70)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        
        # Loop Indicator (Left Bar)
        if is_looping:
            self.loop_bar = QFrame()
            self.loop_bar.setFixedWidth(6)
            self.loop_bar.setStyleSheet(f"background-color: {loop_color or '#3B82F6'}; border-radius: 3px;")
            layout.addWidget(self.loop_bar)
        
        # Index
        self.lbl_idx = QLabel(str(index))
        self.lbl_idx.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 16px; min-width: 25px;")
        layout.addWidget(self.lbl_idx)
        
        # Icon/Type Area
        self.info_container = QWidget()
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        type_name = step_type.replace("_", " ").title()
        self.lbl_type = QLabel(type_name)
        self.lbl_type.setStyleSheet("font-weight: 700; color: #1E293B; font-size: 13px;")
        
        self.lbl_params = QLabel(params_summary)
        self.lbl_params.setStyleSheet("color: #64748B; font-size: 11px;")
        
        info_layout.addWidget(self.lbl_type)
        info_layout.addWidget(self.lbl_params)
        layout.addWidget(self.info_container)
        layout.addStretch()
        
        # Action Buttons
        self.btn_edit = QPushButton("Edit")
        self.btn_del = QPushButton("Delete")
        
        btn_style = """
            QPushButton {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
                color: #475569;
            }
            QPushButton:hover { background-color: #F1F5F9; color: #1E293B; }
        """
        self.btn_edit.setStyleSheet(btn_style)
        self.btn_del.setStyleSheet(btn_style + "QPushButton:hover { color: #EF4444; background-color: #FEE2E2; }")
        
        self.btn_edit.clicked.connect(self.edit_clicked.emit)
        self.btn_del.clicked.connect(self.delete_clicked.emit)
        
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)
        
        self.setStyleSheet("""
            QFrame#step_card {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
            QFrame#step_card:hover {
                border-color: #3B82F6;
                background-color: #F8FAFC;
            }
        """)

class PaletteListWidget(QListWidget):
    """Custom ListWidget for the palette that supports dragging."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSpacing(5)
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 5px;
                color: #475569;
                font-weight: 600;
            }
            QListWidget::item:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return
        
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(item.data(Qt.UserRole))
        drag.setMimeData(mime)
        
        # Pixmap for dragging
        pixmap = item.listWidget().viewport().grab(self.visualItemRect(item))
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width()/2, pixmap.height()/2))
        
        drag.exec_(supportedActions)

class SequenceListWidget(QListWidget):
    """Custom ListWidget for the sequence that supports drops and reordering."""
    order_changed = Signal()
    step_dropped = Signal(str, int) # step_type, row_idx
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSpacing(8)
        self.setViewportMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QListWidget {
                background-color: #F8FAFC;
                border: 2px dashed #E2E8F0;
                border-radius: 12px;
                padding: 10px;
                outline: none;
            }
            QListWidget::item { border: none; }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() or event.source() == self:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() or event.source() == self:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() == self:
            old_row = self.currentRow()
            super().dropEvent(event)
            new_row = self.currentRow()
            if old_row != new_row:
                self.order_changed.emit()
        else:
            step_type = event.mimeData().text()
            row = self.indexAt(event.position().toPoint()).row()
            if row == -1: row = self.count()
            self.step_dropped.emit(step_type, row)
            event.accept()

class ConfigPage(QWidget, Ui_ConfigPage):
    suitesChanged = Signal()
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        
        # Replace default lists with custom ones for D&D
        self.palette_section.removeWidget(self.list_palette)
        self.list_palette.deleteLater()
        self.list_palette = PaletteListWidget(self)
        self.palette_section.addWidget(self.list_palette)
        
        self.editor_layout.removeWidget(self.list_steps_sequence)
        self.list_steps_sequence.deleteLater()
        self.list_steps_sequence = SequenceListWidget(self)
        self.editor_layout.insertWidget(4, self.list_steps_sequence)
        
        self.device_manager = device_manager
        self.db = device_manager.database_service
        self.main_window = main_window
        
        self.current_suite_id = None
        self.steps_data = [] # List of dicts
        
        self._setup_palette()
        self._connect_signals()
        self._load_suites()
        self._apply_styles()

    def _setup_palette(self):
        for stype in StepRegistry.get_all_types():
            desc = StepRegistry.get_description(stype)
            item = QListWidgetItem(stype.replace("_", " ").title())
            item.setData(Qt.UserRole, stype)
            item.setToolTip(desc)
            self.list_palette.addItem(item)

    def _apply_styles(self):
        self.sidebar_container.setStyleSheet("""
            QFrame#sidebar_container {
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QListWidget {
                background: transparent;
                border: none;
                color: #475569;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 8px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #3B82F6;
                color: white;
                font-weight: 600;
            }
            QListWidget::item:hover:!selected {
                background-color: #E2E8F0;
            }
            QLabel { color: #1E293B; }
        """)
        
        self.editor_container.setStyleSheet("""
            QFrame#editor_container {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QLabel { color: #334155; font-weight: 500; }
            QLineEdit, QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #0F172A;
                padding: 10px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3B82F6;
            }
            QTableWidget {
                background-color: #FFFFFF;
                gridline-color: #F1F5F9;
                color: #1E293B;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                padding: 8px;
                border-bottom: 2px solid #E2E8F0;
                border-right: none;
                font-weight: 700;
                text-transform: uppercase;
                font-size: 11px;
            }
            QPushButton#btn_new_suite, QPushButton#btn_add_step {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #475569;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton#btn_new_suite:hover, QPushButton#btn_add_step:hover {
                background-color: #E2E8F0;
            }
        """)

    def _connect_signals(self):
        self.list_suites.currentRowChanged.connect(self._on_suite_selected)
        self.btn_new_suite.clicked.connect(self._on_new_suite)
        self.btn_add_step.clicked.connect(self._on_add_step)
        self.btn_save_suite.clicked.connect(self._on_save_suite)
        self.btn_delete_suite.clicked.connect(self._on_delete_suite)
        
        # New D&D signals
        self.list_steps_sequence.step_dropped.connect(self._on_step_dropped)
        self.list_steps_sequence.order_changed.connect(self._on_steps_reordered)

    def _load_suites(self):
        self.list_suites.clear()
        suites = self.db.get_all_test_suites()
        for s in suites:
            item = QTableWidgetItem(s['name'])
            item.setData(Qt.UserRole, s['id'])
            self.list_suites.addItem(s['name'])
            self.list_suites.item(self.list_suites.count()-1).setData(Qt.UserRole, s['id'])

    def _on_suite_selected(self, row):
        if row < 0: return
        item = self.list_suites.item(row)
        suite_id = item.data(Qt.UserRole)
        self.current_suite_id = suite_id
        
        # Fetch details
        suites = self.db.get_all_test_suites()
        suite_meta = next((s for s in suites if s['id'] == suite_id), None)
        
        if suite_meta:
            self.input_suite_name.setText(suite_meta['name'])
            self.input_suite_desc.setText(suite_meta['description'])
            
            steps_raw = self.db.get_test_suite_steps(suite_id)
            self.steps_data = []
            for s in steps_raw:
                params = json.loads(s['parameters_json']) if isinstance(s['parameters_json'], str) else s['parameters_json']
                self.steps_data.append({
                    "step_type": s['step_type'],
                    "parameters": params,
                    "weight": s['weight'],
                    "estimated_duration": s['estimated_duration']
                })
            self._update_sequence_list()

    def _on_new_suite(self):
        self.current_suite_id = None
        self.input_suite_name.clear()
        self.input_suite_desc.clear()
        self.steps_data = []
        self._update_sequence_list()
        self.list_suites.clearSelection()

    def _update_sequence_list(self):
        self.list_steps_sequence.clear()
        
        # Determine loop ranges for visualization
        loop_map = {} # step_idx -> color
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
        
        repeat_steps = [s for s in self.steps_data if s['step_type'] == "REPEAT"]
        for i, rs in enumerate(repeat_steps):
            start = rs['parameters'].get('start_step', 1) - 1
            end = rs['parameters'].get('end_step', 1) - 1
            color = colors[i % len(colors)]
            for idx in range(start, end + 1):
                loop_map[idx] = color

        for i, step in enumerate(self.steps_data):
            item = QListWidgetItem(self.list_steps_sequence)
            
            params_summary = self._format_parameters(step['step_type'], step['parameters'])
            is_looping = i in loop_map
            loop_color = loop_map.get(i)
            
            card = StepCardWidget(i + 1, step['step_type'], params_summary, is_looping, loop_color)
            card.edit_clicked.connect(lambda r=i: self._edit_step(r))
            card.delete_clicked.connect(lambda r=i: self._delete_step(r))
            
            item.setData(Qt.UserRole, i)
            item.setSizeHint(card.sizeHint())
            self.list_steps_sequence.addItem(item)
            self.list_steps_sequence.setItemWidget(item, card)

    def _format_parameters(self, step_type: str, params: dict) -> str:
        """Formats raw parameters into a human-readable string."""
        if not params: return "N/A"
        
        parts = []
        if step_type == "SET_SOURCE":
            parts.append(f"{params.get('voltage', 0)}V")
            parts.append(f"{params.get('current', 0)}A")
            parts.append(f"PF:{params.get('pf', 1)}")
        elif step_type == "TURN_LOAD":
            parts.append("ON" if params.get("state") else "OFF")
        elif step_type == "WAIT":
            parts.append(f"{params.get('duration_sec', 0)}s")
        elif step_type == "READ_METER" or step_type == "READ_MFM_METER":
            if isinstance(params.get('registers'), str):
                 parts.append(f"Regs: {params.get('registers', '')}")
            else:
                 parts.append(f"Regs: {', '.join(params.get('registers', []))}")
        elif step_type == "PROMPT_USER":
            parts.append(f"'{params.get('message', '')}'")
            if params.get("requires_input"): parts.append("(Input Req)")
        elif step_type == "WAIT_UNTIL_ZERO":
            parts.append(f"<{params.get('threshold', 0.1)}A")
            parts.append(f"Timeout: {params.get('timeout_sec', 30)}s")
        elif step_type == "REPEAT":
            parts.append(f"Steps {params.get('start_step', 1)}-{params.get('end_step', 1)}")
            parts.append(f"x{params.get('iterations', 1)}")
        else:
            return str(params)
            
        return " | ".join(parts)

    def _on_add_step(self):
        dialog = StepEditDialog(self)
        if dialog.exec():
            self.steps_data.append(dialog.get_data())
            self._update_sequence_list()

    def _on_step_dropped(self, step_type, row_idx):
        # Create default parameters for the new step
        default_params = StepRegistry.get_default_params(step_type)
        
        new_step = {"step_type": step_type, "parameters": default_params}
        self.steps_data.insert(row_idx, new_step)
        self._update_sequence_list()

    def _on_steps_reordered(self):
        # Re-sync steps_data with the list order
        reordered_data = []
        for i in range(self.list_steps_sequence.count()):
            item = self.list_steps_sequence.item(i)
            orig_idx = item.data(Qt.UserRole)
            reordered_data.append(self.steps_data[orig_idx])
        
        self.steps_data = reordered_data
        self._update_sequence_list()

    def _edit_step(self, row_idx):
        dialog = StepEditDialog(self, self.steps_data[row_idx])
        if dialog.exec():
            self.steps_data[row_idx] = dialog.get_data()
            self._update_sequence_list()

    def _delete_step(self, row_idx):
        self.steps_data.pop(row_idx)
        self._update_sequence_list()

    def _on_save_suite(self):
        name = self.input_suite_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Suite name is required.")
            return
            
        desc = self.input_suite_desc.toPlainText()
        
        try:
            new_id = self.db.save_test_suite(name, desc, self.steps_data, self.current_suite_id)
            self.current_suite_id = new_id
            self.main_window.append_log("INFO", f"Test Suite '{name}' saved successfully.")
            self._load_suites()
            self.suitesChanged.emit() # Notify other pages
            # Select the saved suite
            for i in range(self.list_suites.count()):
                if self.list_suites.item(i).data(Qt.UserRole) == self.current_suite_id:
                    self.list_suites.setCurrentRow(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save suite: {e}")

    def _on_delete_suite(self):
        if not self.current_suite_id: return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   "Are you sure you want to delete this test suite?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_test_suite(self.current_suite_id)
                self.main_window.append_log("INFO", "Test Suite deleted.")
                self._load_suites()
                self._on_new_suite()
                self.suitesChanged.emit() # Notify other pages
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete suite: {e}")
