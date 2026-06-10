import os
import sys
from PySide6.QtWidgets import QMainWindow, QGraphicsOpacityEffect
from PySide6.QtCore import Slot, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QColor

from ui.ui_main_window import Ui_MainWindow
from ui.pages.test_page import TestPage
from ui.pages.logs_page import LogsPage
from ui.pages.settings_page import SettingsPage
from ui.pages.debug_page import DebugPage
from ui.pages.reports_page import ReportsPage
from ui.pages.sequence_viewer_page import SequenceViewerPage
from ui.pages.meter_profiles_page import MeterProfilesPage

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main shell for the application with a toggleable sidebar and page navigation.
    """
    def __init__(self, device_manager):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.current_theme = "light"
        
        # 1. Initialize Pages
        self.test_page = TestPage(device_manager, self)
        self.logs_page = LogsPage(self)
        self.settings_page = SettingsPage(device_manager, self)
        self.debug_page = DebugPage()
        self.reports_page = ReportsPage()
        self.sequence_viewer_page = SequenceViewerPage(device_manager, self)
        self.meter_profiles_page = MeterProfilesPage(self)
        self.settings_page = SettingsPage(device_manager, self)
        
        # 2. Add to Stacked Widget
        self.stacked_widget.addWidget(self.test_page)
        self.stacked_widget.addWidget(self.logs_page)
        self.stacked_widget.addWidget(self.debug_page)
        self.stacked_widget.addWidget(self.reports_page)
        self.stacked_widget.addWidget(self.sequence_viewer_page)
        self.stacked_widget.addWidget(self.meter_profiles_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        # 3. Sidebar State & Timer
        self.sidebar_expanded = False
        self._current_animations = []
        self.collapse_timer = QTimer()
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(lambda: self._animate_sidebar(False))
        
        # 4. Setup Navigation & Effects
        self._setup_navigation()
        self._setup_sidebar_effects()
        self._load_theme()
        
        # 5. Connect Page Signals for dynamic updates
        # (Config page removed)
        
        # 6. Connect Events
        self.frame_sidebar.installEventFilter(self)
        self._animate_sidebar(False, instant=True)
        
        # Hide config navigation -> Now we show it for Sequence Viewer
        if hasattr(self, 'nav_item_config'):
            self.nav_item_config.show()
        
    def _setup_navigation(self):
        # 1. Sidebar Toggle (Pancake)
        self.btn_sidebar_toggle.clicked.connect(lambda: self._animate_sidebar(not self.sidebar_expanded))
        
        # 2. Click signals for the icons (Buttons)
        self.btn_nav_test.clicked.connect(lambda: self._switch_page(1, "Test Dashboard"))
        self.btn_nav_logs.clicked.connect(lambda: self._switch_page(2, "System Logs"))
        self.btn_nav_debug.clicked.connect(lambda: self._switch_page(3, "Debug Screen"))
        self.btn_nav_reports.clicked.connect(lambda: self._switch_page(4, "Reports"))
        self.btn_nav_config.clicked.connect(lambda: self._switch_page(5, "Sequence Viewer"))
        
        # Dynamically add Meter Profiles navigation
        self._add_dynamic_nav_item()
        
        self.btn_nav_settings.clicked.connect(lambda: self._switch_page(7, "Settings"))
        
        # 3. Make the entire frames clickable (via event filters)
        self.nav_item_test.installEventFilter(self)
        self.nav_item_logs.installEventFilter(self)
        self.nav_item_debug.installEventFilter(self)
        self.nav_item_reports.installEventFilter(self)
        self.nav_item_config.installEventFilter(self)
        self.nav_item_profiles.installEventFilter(self)
        self.nav_item_settings.installEventFilter(self)
        
        # Initial page
        self._switch_page(1, "Test Dashboard")

    def _add_dynamic_nav_item(self):
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel, QSizePolicy
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QCursor
        
        self.nav_item_profiles = QFrame(self.frame_sidebar)
        self.nav_item_profiles.setObjectName(u"nav_item_profiles")
        self.nav_item_profiles.setMinimumSize(QSize(0, 50))
        self.nav_item_profiles.setMaximumSize(QSize(16777215, 50))
        self.nav_item_profiles.setCursor(QCursor(Qt.PointingHandCursor))
        self.nav_item_profiles.setStyleSheet(u"QFrame:hover { background-color: rgba(255, 255, 255, 0.05); border-radius: 8px; }")
        
        hLayout = QHBoxLayout(self.nav_item_profiles)
        hLayout.setSpacing(15)
        hLayout.setObjectName(u"hLayout_profiles")
        hLayout.setContentsMargins(10, 0, 0, 0)
        
        self.btn_nav_profiles = QPushButton(self.nav_item_profiles)
        self.btn_nav_profiles.setObjectName(u"btn_nav_profiles")
        self.btn_nav_profiles.setMinimumSize(QSize(50, 50))
        self.btn_nav_profiles.setMaximumSize(QSize(50, 50))
        hLayout.addWidget(self.btn_nav_profiles)
        
        self.lbl_nav_profiles = QLabel(self.nav_item_profiles)
        self.lbl_nav_profiles.setObjectName(u"lbl_nav_profiles")
        self.lbl_nav_profiles.setText("Meter Profiles")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lbl_nav_profiles.setSizePolicy(sizePolicy)
        hLayout.addWidget(self.lbl_nav_profiles)
        
        # Insert before Settings
        layout = self.frame_sidebar.layout()
        settings_idx = layout.indexOf(self.nav_item_settings)
        layout.insertWidget(settings_idx, self.nav_item_profiles)
        
        self.btn_nav_profiles.clicked.connect(lambda: self._switch_page(6, "Meter Profiles"))

    def _setup_sidebar_effects(self):
        """Initializes opacity effects for labels."""
        self.nav_labels = [
            self.lbl_nav_test, self.lbl_nav_logs, self.lbl_nav_debug, 
            self.lbl_nav_reports, self.lbl_nav_config, self.lbl_nav_profiles, self.lbl_nav_settings
        ]
        self.label_effects = []
        for lbl in self.nav_labels:
            effect = QGraphicsOpacityEffect(lbl)
            lbl.setGraphicsEffect(effect)
            self.label_effects.append(effect)

    def _switch_page(self, index, title):
        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)
        
        # Requirement: Collapse sidebar on page change
        if self.sidebar_expanded:
            self._animate_sidebar(False)

    def _load_theme(self):
        theme_file = "dark_theme.qss" if self.current_theme == "dark" else "light_theme.qss"
        theme_path = os.path.join(os.path.dirname(__file__), "resources", "css", theme_file)
        try:
            with open(theme_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load theme: {e}")
            
        # Re-apply sidebar state styling
        self._apply_sidebar_style(self.sidebar_expanded)

    @Slot()
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._load_theme()

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        self.logs_page.append_log(level, message)

    @Slot(str, str)
    def update_hardware_status(self, module: str, message: str):
        self.lbl_hw_status.setText(f"HW: {module} - {message}")
        if "EMERGENCY" in message or "STOP" in message:
            self.lbl_hw_status.setStyleSheet("color: #F87171; font-weight: bold;")
        else:
            self.lbl_hw_status.setStyleSheet("")

    @Slot()
    def trigger_emergency_stop(self):
        self.append_log("ERROR", "MANUAL EMERGENCY STOP TRIGGERED!")
        self.update_hardware_status("SYSTEM", "EMERGENCY STOP")
        self.test_page.btn_start.setEnabled(False)
        self.test_page.btn_stop.setEnabled(False)
        self.test_page.btn_abort.setEnabled(False)
        if self.test_page.test_runner:
            self.test_page.test_runner.cancel()

    @Slot()
    def handle_emergency_triggered(self):
        self.trigger_emergency_stop()

    def eventFilter(self, obj, event):
        # Handle Sidebar Timer (15s auto-collapse on leave)
        if obj == self.frame_sidebar:
            if event.type() == event.Type.Enter:
                self.collapse_timer.stop() # Cancel collapse if mouse returns
            elif event.type() == event.Type.Leave:
                if self.sidebar_expanded:
                    self.collapse_timer.start(15000) # 15 seconds
        
        # Handle Navigation Clicks on the entire row
        elif event.type() == event.Type.MouseButtonPress:
            if obj == self.nav_item_test:
                self._switch_page(1, "Test Dashboard")
            elif obj == self.nav_item_logs:
                self._switch_page(2, "System Logs")
            elif obj == self.nav_item_debug:
                self._switch_page(3, "Debug Screen")
            elif obj == self.nav_item_reports:
                self._switch_page(4, "Reports")
            elif obj == self.nav_item_config:
                self._switch_page(5, "Sequence Viewer")
            elif obj == self.nav_item_profiles:
                self._switch_page(6, "Meter Profiles")
            elif obj == self.nav_item_settings:
                self._switch_page(7, "Settings")
                
        return super().eventFilter(obj, event)

    def _animate_sidebar(self, expand: bool, instant: bool = False):
        if not instant and expand == self.sidebar_expanded: return
        self.sidebar_expanded = expand
        
        # Reset timer if manually collapsed
        if not expand:
            self.collapse_timer.stop()
            
        width = 250 if expand else 70
        duration = 0 if instant else 350
        opacity = 1.0 if expand else 0.0
        
        # 1. Animate Width
        self.animation = QPropertyAnimation(self.frame_sidebar, b"minimumWidth")
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.frame_sidebar.width())
        self.animation.setEndValue(width)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuint)
        
        self.animation_max = QPropertyAnimation(self.frame_sidebar, b"maximumWidth")
        self.animation_max.setDuration(duration)
        self.animation_max.setStartValue(self.frame_sidebar.width())
        self.animation_max.setEndValue(width)
        self.animation_max.setEasingCurve(QEasingCurve.Type.OutQuint)
        
        self.group = QParallelAnimationGroup()
        self.group.addAnimation(self.animation)
        self.group.addAnimation(self.animation_max)
        
        # 2. Animate Opacity for Labels
        self._current_animations = []
        for effect in self.label_effects:
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(effect.opacity())
            anim.setEndValue(opacity)
            self.group.addAnimation(anim)
            self._current_animations.append(anim)
        
        # 3. Apply Styles
        self._apply_sidebar_style(expand)
        
        if instant:
            self.frame_sidebar.setMinimumWidth(width)
            self.frame_sidebar.setMaximumWidth(width)
            for effect in self.label_effects:
                effect.setOpacity(opacity)
        else:
            self.group.start()

    def _apply_sidebar_style(self, expand: bool):
        """Ensures icons stay fixed and professional."""
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        
        icons_dir = os.path.join(os.path.dirname(__file__), "resources", "icons")
        
        # Style the Toggle Button (Dynamic Icon: Menu vs Cross)
        toggle_icon_file = "cross.png" if expand else "menu.png"
        toggle_icon_path = os.path.join(icons_dir, toggle_icon_file)
        self.btn_sidebar_toggle.setIcon(QIcon(toggle_icon_path))
        self.btn_sidebar_toggle.setIconSize(QSize(32, 32))
        self.btn_sidebar_toggle.setText("")
        
        self.btn_sidebar_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)

        buttons = [
            (self.btn_nav_test, "dashboard.png"),
            (self.btn_nav_logs, "logs.png"),
            (self.btn_nav_debug, "debug.png"),
            (self.btn_nav_reports, "reports.png"),
            (self.btn_nav_config, "configuration.png"),
            (self.btn_nav_profiles, "meter.png"),
            (self.btn_nav_settings, "settings.png")
        ]
        
        # Centered padding: (70/2 - 32/2) = 19px
        # Expanded padding: Shift right to reduce gap (30px)
        # Note: We now have 10px frame margin, so button is in 50px wide container.
        # Button is 50px, Icon is 32px. Center is 50/2 - 32/2 = 9px.
        padding = 9
        
        for btn, icon_file in buttons:
            icon_path = os.path.join(icons_dir, icon_file)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
            btn.setText("")
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    text-align: center;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                }}
            """)
        
        for lbl in self.nav_labels:
            lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #475569; padding-left: 0px; margin-left: 0px;")

    def closeEvent(self, event):
        self.device_manager.cleanup()
        super().closeEvent(event)
