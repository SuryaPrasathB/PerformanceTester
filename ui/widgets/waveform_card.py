import math
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QFont

from ui.widgets.waveform_graph import WaveformGraph

class WaveformPreview(QFrame):
    """Simple miniature preview canvas displaying only the waveform line."""
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 4px;")
        self.setMinimumHeight(100)
        self.setMinimumWidth(150)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.data or len(self.data) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Determine min/max values for scaling
        max_val = max(self.data)
        min_val = min(self.data)
        span = max_val - min_val
        if span == 0.0:
            span = 1.0
            
        # Draw gridless zero-axis line
        painter.setPen(QPen(QColor("#F1F5F9"), 1))
        zero_ratio = (0.0 - min_val) / span
        zero_y = h - int(zero_ratio * h)
        zero_y = max(2, min(h - 2, zero_y))
        painter.drawLine(0, zero_y, w, zero_y)
        
        # Draw waveform path
        painter.setPen(QPen(QColor("#2563EB"), 1.5))
        
        # Downsample for faster performance
        step = max(1, len(self.data) // w)
        last_pt = None
        
        for idx in range(0, len(self.data), step):
            px = (idx / len(self.data)) * w
            val = self.data[idx]
            
            ratio = (val - min_val) / span
            py = h - (ratio * h)
            # Clip padding
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
    
    def __init__(self, name, data, timebase, range_val, parent=None):
        super().__init__(parent)
        self.name = name
        self.data = data
        self.timebase = timebase
        self.range_val = range_val
        
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("WaveformCard")
        self.setFixedWidth(240)
        self.setFixedHeight(230)
        
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
        
        self.lbl_title = QLabel(name)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 12px;")
        layout.addWidget(self.lbl_title)
        
        self.preview = WaveformPreview(data, self)
        layout.addWidget(self.preview)

    def mousePressEvent(self, event):
        """Launches the detailed interactive expanded view dialog."""
        self.open_analysis_dialog()

    def open_analysis_dialog(self):
        """Builds and shows the expanded analysis modal."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Waveform Analysis - {self.name}")
        dialog.setMinimumSize(950, 650)
        dialog.resize(1000, 700)
        dialog.setStyleSheet("background-color: #F8FAFC;")
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Interactive Graph widget
        graph = WaveformGraph(dialog)
        graph.setData(self.data, None, self.timebase, self.range_val)
        # Enable Auto-zoom by default for transient capture views
        graph.setAutoZoomEnabled(True)
        main_layout.addWidget(graph)
        
        # Toolbar layout
        toolbar = QFrame(dialog)
        toolbar.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
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
        
        # Display the dialog
        dialog.exec()
