import math
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPoint, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QFont
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QFont

from ui.widgets.waveform_graph import WaveformGraph

class WaveformPreview(QFrame):
    """Simple miniature preview canvas displaying only the waveform line."""
    
    def __init__(self, data, start_idx=0, end_idx=None, parent=None):
        super().__init__(parent)
        self.data = data
        self.start_idx = start_idx
        self.end_idx = end_idx if end_idx is not None else (len(data[0]) if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list) else len(data))
        self.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 4px;")
        self.setMinimumHeight(100)
        self.setMinimumWidth(150)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        data_a = self.data
        data_b = None
        if isinstance(self.data, list) and len(self.data) == 2 and isinstance(self.data[0], list):
            data_a = self.data[0]
            data_b = self.data[1]

        if not data_a or len(data_a) < 2:
            return
            
        data_a = data_a[self.start_idx:self.end_idx]
        if data_b:
            data_b = data_b[self.start_idx:self.end_idx]
            
        if len(data_a) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Determine min/max values for scaling data_a
        max_val_a = max(data_a)
        min_val_a = min(data_a)
        abs_max_a = max(abs(max_val_a), abs(min_val_a))
        if abs_max_a == 0.0:
            abs_max_a = 1.0
            
        # Force symmetry so the waveform is perfectly centered
        max_val_a = abs_max_a
        min_val_a = -abs_max_a
        span_a = max_val_a - min_val_a
            
        # Draw gridless zero-axis line
        painter.setPen(QPen(QColor("#F1F5F9"), 1))
        zero_ratio_a = (0.0 - min_val_a) / span_a
        zero_y = h - int(zero_ratio_a * h)
        zero_y = max(2, min(h - 2, zero_y))
        painter.drawLine(0, zero_y, w, zero_y)
        
        # Draw data_a (Blue)
        painter.setPen(QPen(QColor("#2563EB"), 1.2))
        step = max(1, len(data_a) // w)
        last_pt = None
        
        for idx in range(0, len(data_a), step):
            px = (idx / len(data_a)) * w
            val = data_a[idx]
            
            ratio = (val - min_val_a) / span_a
            py = h - (ratio * h)
            # Clip padding
            py = max(4, min(h - 4, py))
            
            curr_pt = QPoint(int(px), int(py))
            if last_pt is not None:
                painter.drawLine(last_pt, curr_pt)
            last_pt = curr_pt

        # Draw data_b (Red) if present
        if data_b and len(data_b) >= 2:
            max_val_b = max(data_b)
            min_val_b = min(data_b)
            abs_max_b = max(abs(max_val_b), abs(min_val_b))
            if abs_max_b == 0.0:
                abs_max_b = 1.0
                
            max_val_b = abs_max_b
            min_val_b = -abs_max_b
            span_b = max_val_b - min_val_b
                
            painter.setPen(QPen(QColor("#EF4444"), 1.2))
            last_pt = None
            
            for idx in range(0, len(data_b), step):
                px = (idx / len(data_b)) * w
                val = data_b[idx]
                
                ratio = (val - min_val_b) / span_b
                py = h - (ratio * h)
                py = max(4, min(h - 4, py))
                
                curr_pt = QPoint(int(px), int(py))
                if last_pt is not None:
                    painter.drawLine(last_pt, curr_pt)
                last_pt = curr_pt


class WaveformCard(QFrame):
    """
    Card UI widget containing a title, miniature preview, and click-to-analyze 
    trigger that opens the detailed analysis view in a QDialog.
    """
    override_requested = Signal(dict)
    redo_requested = Signal(str)
    
    _active_dialog = None
    
    def __init__(self, name, data, timebase, range_val, parent=None, test_id="unknown"):
        super().__init__(parent)
        self.name = name
        self.data = data
        self.timebase = timebase
        self.range_val = range_val
        self.test_id = test_id.lower() if test_id else "unknown"
        
        # Calculate PF and Measured Current if dual channels are present and it's not G5 test
        self.calculated_pf = None
        self.pulse_duration = None
        self.measured_current = None
        self.peak_voltage = None
        
        data_a = self.data
        data_b = None
        if isinstance(self.data, list) and len(self.data) == 2 and isinstance(self.data[0], list):
            data_a = self.data[0]
            data_b = self.data[1]
            
        if data_b and self.test_id != "g5":
            try:
                from core.waveform_analyzer import calculate_pulse_duration, calculate_pf_from_duration, calculate_peak_voltage, calculate_measured_current
                duration_ms = calculate_pulse_duration(data_b, timebase)
                if duration_ms > 0.0:
                    self.pulse_duration = duration_ms
                    self.calculated_pf = calculate_pf_from_duration(duration_ms)
                
                self.peak_voltage = calculate_peak_voltage(data_b)
                self.measured_current = calculate_measured_current(self.peak_voltage)
            except Exception:
                pass

        
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("WaveformCard")
        self.setFixedWidth(240)
        self.setMinimumHeight(220)
        

        
        # Premium styling
        self.setStyleSheet("""
            #WaveformCard {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
            }
            #WaveformCard:hover {
                background-color: #F1F5F9;
                border: 1px solid #3B82F6;
            }
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(15, 23, 42, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        
        # Title at the top left
        self.lbl_title = QLabel(name)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 12px;")
        layout.addWidget(self.lbl_title)
        
        # Calculate zoomed indices using WaveformGraph logic
        start_idx = 0
        end_idx = None
        try:
            # Instantiate dummy graph to borrow the robust detection logic
            graph = WaveformGraph()
            graph.set_data(data, timebase, range_val)
            if graph.view_end_time_ms > 0:
                start_idx = max(0, int(graph.view_start_time_ms / graph.interval_ms))
                end_idx = min(len(data_a), int(graph.view_end_time_ms / graph.interval_ms))
                # Add a tiny bit of extra padding for the minimap specifically
                pad = max(2, int((end_idx - start_idx) * 0.1))
                start_idx = max(0, start_idx - pad)
                end_idx = min(len(data_a), end_idx + pad)
        except Exception as e:
            print(f"Error calculating zoom for minimap: {e}")
        
        # Graph takes up the most space
        self.preview = WaveformPreview(data, start_idx, end_idx, self)
        layout.addWidget(self.preview, stretch=1)
        
        # PF & Measured Current label below the graph
        if self.calculated_pf is not None or self.measured_current is not None:
            text_parts = []
            if self.calculated_pf is not None:
                text_parts.append(f"PF: {self.calculated_pf:.2f}")
            if self.measured_current is not None:
                text_parts.append(f"Curr: {self.measured_current:.1f}A")
            
            self.lbl_pf = QLabel(" | ".join(text_parts))
            self.lbl_pf.setStyleSheet("font-weight: bold; color: #10B981; font-size: 11px;")
            self.lbl_pf.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.lbl_pf)

        # Add Redo Button at the bottom
        from PySide6.QtWidgets import QPushButton
        self.btn_redo = QPushButton("Redo Test", self)
        self.btn_redo.setFixedSize(120, 28)
        self.btn_redo.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                color: #EF4444;
                border: 1px solid #F87171;
                font-weight: bold;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
            }
            QPushButton:pressed {
                background-color: #FECACA;
            }
        """)
        layout.addWidget(self.btn_redo, alignment=Qt.AlignCenter)
        self.btn_redo.hide()
        self.btn_redo.clicked.connect(lambda: self.redo_requested.emit(self.name))
        self.in_review_mode = False

    def set_review_mode(self, enabled):
        self.in_review_mode = enabled
        if enabled:
            self.btn_redo.show()
        else:
            self.btn_redo.hide()

    def mousePressEvent(self, event):
        """Launches the detailed interactive expanded view dialog on left click."""
        if event.button() == Qt.LeftButton:
            # Prevent opening the dialog if the user clicked on or very close to the redo button
            if self.btn_redo.isVisible() and self.btn_redo.geometry().adjusted(-5, -5, 5, 5).contains(event.pos()):
                return
            self.open_analysis_dialog()



    def open_analysis_dialog(self):
        """Builds and shows the expanded analysis modal."""
        if WaveformCard._active_dialog is not None and WaveformCard._active_dialog.isVisible():
            WaveformCard._active_dialog.raise_()
            WaveformCard._active_dialog.activateWindow()
            return
            
        dialog = QDialog(self.window(), Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setWindowTitle(f"Waveform Analysis - {self.name}")
        dialog.setMinimumSize(950, 650)
        dialog.setStyleSheet("background-color: #F8FAFC;")
        WaveformCard._active_dialog = dialog

        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Interactive Graph widget
        graph = WaveformGraph(dialog)
        graph.setData(self.data, None, self.timebase, self.range_val, test_id=self.test_id)
        
        # Inject the overrides/initial calculations into the graph so its floating badge renders correctly
        graph.calculated_pf = self.calculated_pf
        graph.measured_current = self.measured_current
        graph.pulse_duration = self.pulse_duration
        
        # Auto-zoom and state restoration will happen after toolbar buttons are created
        main_layout.addWidget(graph, stretch=1)
        
        # Toolbar layout
        toolbar = QFrame(dialog)
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 2px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(15)
        
        btn_autozoom = QPushButton("AUTO ZOOM", toolbar)
        btn_autozoom.setCheckable(True)
        btn_autozoom.setChecked(True)
        btn_autozoom.setMinimumHeight(32)
        btn_autozoom.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 12px;
                padding-right: 12px;
            }
            QPushButton:checked {
                background-color: #2563EB;
                color: white;
                border: 1px solid #2563EB;
            }
        """)
        btn_autozoom.toggled.connect(graph.setAutoZoomEnabled)
        tb_layout.addWidget(btn_autozoom)
        
        # Restore saved state if it exists, otherwise initialize defaults
        if hasattr(self, 'saved_graph_state'):
            s = self.saved_graph_state
            graph.cursor1_t = s['c1_t']
            graph.cursor2_t = s['c2_t']
            graph.cursor_y1_val = s['y1_v']
            graph.cursor_y2_val = s['y2_v']
            graph.view_start_time_ms = s['v_s']
            graph.view_end_time_ms = s['v_e']
            graph.view_min_volt = s['v_min_v']
            graph.view_max_volt = s['v_max_v']
            graph.view_min_curr = s['v_min_c']
            graph.view_max_curr = s['v_max_c']
            graph.meas_box_pos = s['meas_pos']
            
            btn_autozoom.blockSignals(True)
            btn_autozoom.setChecked(s['auto_zoom'])
            graph.auto_zoom_enabled = s['auto_zoom']
            btn_autozoom.blockSignals(False)
            
            graph._auto_position_cursors = False
            graph.clamp_view()
        else:
            btn_autozoom.setChecked(True)
            graph.setAutoZoomEnabled(True)
        
        btn_reset = QPushButton("RESET ZOOM", toolbar)
        btn_reset.setMinimumHeight(32)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 12px;
                padding-right: 12px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
            }
        """)
        btn_reset.clicked.connect(lambda: [btn_autozoom.setChecked(False), graph.reset_zoom(), graph.update()])
        tb_layout.addWidget(btn_reset)
        
        lbl_hint = QLabel("Analysis Mode: Drag vertical/horizontal cursors to measure peaks and frequencies.", toolbar)
        lbl_hint.setStyleSheet("color: #64748B; font-style: italic; font-size: 12px;")
        tb_layout.addWidget(lbl_hint)
        
        tb_layout.addStretch()
        
        if self.calculated_pf is not None:
            lbl_pf_val = QLabel(f"Calculated PF: {self.calculated_pf:.3f} ({self.pulse_duration:.2f} ms)", toolbar)
            lbl_pf_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981; padding-right: 15px;")
            tb_layout.addWidget(lbl_pf_val)
            
            lbl_curr_val = QLabel(f"Measured Current: {self.measured_current:.1f} A", toolbar)
            lbl_curr_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #F59E0B; padding-right: 15px;")
            tb_layout.addWidget(lbl_curr_val)
            
            # Dynamic update on cursor move
            def update_live_labels():
                live_pf = graph.get_override_pf()
                live_curr = graph.get_override_current()
                live_dur = graph.get_override_duration()
                lbl_pf_val.setText(f"Calculated PF: {live_pf:.3f} ({live_dur:.2f} ms)")
                lbl_curr_val.setText(f"Measured Current: {live_curr:.1f} A")
                # Also update the floating badge in the graph
                graph.calculated_pf = live_pf
                graph.measured_current = live_curr
                graph.pulse_duration = live_dur
                
            graph.cursors_moved.connect(update_live_labels)

        btn_save = QPushButton("SAVE OVERRIDE", toolbar)
        btn_save.setMinimumHeight(32)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding-left: 16px;
                padding-right: 16px;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        
        def save_override():
            pf = graph.get_override_pf()
            curr = graph.get_override_current()
            
            # Update local UI
            self.calculated_pf = pf
            self.measured_current = curr
            
            if hasattr(self, 'lbl_pf'):
                self.lbl_pf.setText(f"PF: {pf:.2f} | Curr: {curr:.1f}A")
            
            # Update preview zoom
            if graph.view_end_time_ms > 0:
                s_idx = max(0, int(graph.view_start_time_ms / graph.interval_ms))
                e_idx = min(len(self.data[0]) if isinstance(self.data, list) and len(self.data) > 0 else 0, int(graph.view_end_time_ms / graph.interval_ms))
                self.preview.start_idx = s_idx
                self.preview.end_idx = e_idx
                self.preview.update()
                
            # Grab graph pixmap
            pixmap = graph.grab()
            
            self.override_requested.emit({
                'test_id': self.test_id,
                'pf': pf,
                'current': curr,
                'pixmap': pixmap,
                'name': self.name
            })
            dialog.accept()
            
        btn_save.clicked.connect(save_override)
        tb_layout.addWidget(btn_save)
            
        btn_close = QPushButton("CLOSE", toolbar)
        btn_close.setMinimumHeight(32)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding-left: 16px;
                padding-right: 16px;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
        """)
        btn_close.clicked.connect(dialog.accept)
        tb_layout.addWidget(btn_close)
        
        main_layout.addWidget(toolbar)
        
        # Cleanup when closed
        def cleanup():
            self.saved_graph_state = {
                'c1_t': graph.cursor1_t,
                'c2_t': graph.cursor2_t,
                'y1_v': graph.cursor_y1_val,
                'y2_v': graph.cursor_y2_val,
                'v_s': graph.view_start_time_ms,
                'v_e': graph.view_end_time_ms,
                'v_min_v': graph.view_min_volt,
                'v_max_v': graph.view_max_volt,
                'v_min_c': graph.view_min_curr,
                'v_max_c': graph.view_max_curr,
                'auto_zoom': btn_autozoom.isChecked(),
                'meas_pos': graph.meas_box_pos
            }
            if WaveformCard._active_dialog == dialog:
                WaveformCard._active_dialog = None
        dialog.finished.connect(cleanup)
        
        # Display the dialog
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.exec()
