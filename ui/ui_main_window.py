# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1100, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.header_layout = QHBoxLayout()
        self.header_layout.setObjectName(u"header_layout")
        self.lbl_title = QLabel(self.centralwidget)
        self.lbl_title.setObjectName(u"lbl_title")

        self.header_layout.addWidget(self.lbl_title)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.header_layout.addItem(self.horizontalSpacer)

        self.lbl_hw_status = QLabel(self.centralwidget)
        self.lbl_hw_status.setObjectName(u"lbl_hw_status")

        self.header_layout.addWidget(self.lbl_hw_status)

        self.btn_toggle_theme = QPushButton(self.centralwidget)
        self.btn_toggle_theme.setObjectName(u"btn_toggle_theme")

        self.header_layout.addWidget(self.btn_toggle_theme)


        self.verticalLayout.addLayout(self.header_layout)

        self.splitter_main = QSplitter(self.centralwidget)
        self.splitter_main.setObjectName(u"splitter_main")
        self.splitter_main.setOrientation(Qt.Horizontal)
        self.left_panel = QWidget(self.splitter_main)
        self.left_panel.setObjectName(u"left_panel")
        self.verticalLayout_2 = QVBoxLayout(self.left_panel)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_1 = QLabel(self.left_panel)
        self.label_1.setObjectName(u"label_1")

        self.verticalLayout_2.addWidget(self.label_1)

        self.list_tests = QListWidget(self.left_panel)
        self.list_tests.setObjectName(u"list_tests")

        self.verticalLayout_2.addWidget(self.list_tests)

        self.label_device = QLabel(self.left_panel)
        self.label_device.setObjectName(u"label_device")

        self.verticalLayout_2.addWidget(self.label_device)

        self.table_devices = QTableWidget(self.left_panel)
        self.table_devices.setObjectName(u"table_devices")

        self.verticalLayout_2.addWidget(self.table_devices)

        self.splitter_main.addWidget(self.left_panel)
        self.center_panel = QWidget(self.splitter_main)
        self.center_panel.setObjectName(u"center_panel")
        self.verticalLayout_3 = QVBoxLayout(self.center_panel)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.center_panel)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_2)

        self.verticalSpacerTop = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacerTop)

        self.lbl_instruction = QLabel(self.center_panel)
        self.lbl_instruction.setObjectName(u"lbl_instruction")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.lbl_instruction)

        self.input_instruction = QLineEdit(self.center_panel)
        self.input_instruction.setObjectName(u"input_instruction")

        self.verticalLayout_3.addWidget(self.input_instruction)

        self.btn_done = QPushButton(self.center_panel)
        self.btn_done.setObjectName(u"btn_done")

        self.verticalLayout_3.addWidget(self.btn_done)

        self.verticalSpacerBot = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacerBot)

        self.lbl_live_data = QLabel(self.center_panel)
        self.lbl_live_data.setObjectName(u"lbl_live_data")
        self.lbl_live_data.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lbl_live_data)

        self.progress_bar = QProgressBar(self.center_panel)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)

        self.verticalLayout_3.addWidget(self.progress_bar)

        self.splitter_main.addWidget(self.center_panel)

        self.verticalLayout.addWidget(self.splitter_main)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.txt_logs = QTextEdit(self.centralwidget)
        self.txt_logs.setObjectName(u"txt_logs")
        self.txt_logs.setReadOnly(True)

        self.verticalLayout.addWidget(self.txt_logs)

        self.footer_layout = QHBoxLayout()
        self.footer_layout.setObjectName(u"footer_layout")
        self.btn_start = QPushButton(self.centralwidget)
        self.btn_start.setObjectName(u"btn_start")

        self.footer_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.centralwidget)
        self.btn_stop.setObjectName(u"btn_stop")

        self.footer_layout.addWidget(self.btn_stop)

        self.btn_abort = QPushButton(self.centralwidget)
        self.btn_abort.setObjectName(u"btn_abort")

        self.footer_layout.addWidget(self.btn_abort)

        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footer_layout.addItem(self.horizontalSpacer_2)

        self.btn_connect_all = QPushButton(self.centralwidget)
        self.btn_connect_all.setObjectName(u"btn_connect_all")

        self.footer_layout.addWidget(self.btn_connect_all)

        self.btn_emergency = QPushButton(self.centralwidget)
        self.btn_emergency.setObjectName(u"btn_emergency")

        self.footer_layout.addWidget(self.btn_emergency)


        self.verticalLayout.addLayout(self.footer_layout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Energy Meter Test System", None))
        self.lbl_title.setText(QCoreApplication.translate("MainWindow", u"Meter Test System v2.0", None))
        self.lbl_title.setObjectName(QCoreApplication.translate("MainWindow", u"lbl_title", None))
        self.lbl_hw_status.setText(QCoreApplication.translate("MainWindow", u"HW Status: OK", None))
        self.lbl_hw_status.setObjectName(QCoreApplication.translate("MainWindow", u"lbl_hw_status", None))
        self.btn_toggle_theme.setText(QCoreApplication.translate("MainWindow", u"Toggle Theme", None))
        self.label_1.setText(QCoreApplication.translate("MainWindow", u"Test Selection", None))
        self.label_1.setObjectName(QCoreApplication.translate("MainWindow", u"section_title", None))
        self.label_device.setText(QCoreApplication.translate("MainWindow", u"Devices Status:", None))
        self.label_device.setObjectName(QCoreApplication.translate("MainWindow", u"section_title", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Progress & Instructions", None))
        self.label_2.setObjectName(QCoreApplication.translate("MainWindow", u"section_title", None))
        self.lbl_instruction.setText(QCoreApplication.translate("MainWindow", u"Select a test and press Start...", None))
        self.lbl_instruction.setObjectName(QCoreApplication.translate("MainWindow", u"lbl_instruction", None))
        self.input_instruction.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Waiting for input...", None))
        self.btn_done.setText(QCoreApplication.translate("MainWindow", u"Done / Confirm", None))
        self.btn_done.setObjectName(QCoreApplication.translate("MainWindow", u"btn_done", None))
        self.lbl_live_data.setText(QCoreApplication.translate("MainWindow", u"State: IDLE | V: -- | I: -- | PF: --", None))
        self.lbl_live_data.setObjectName(QCoreApplication.translate("MainWindow", u"lbl_live_data", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Logs & Reports", None))
        self.label_3.setObjectName(QCoreApplication.translate("MainWindow", u"section_title", None))
        self.btn_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.btn_start.setObjectName(QCoreApplication.translate("MainWindow", u"btn_start", None))
        self.btn_stop.setText(QCoreApplication.translate("MainWindow", u"Pause/Resume", None))
        self.btn_abort.setText(QCoreApplication.translate("MainWindow", u"Abort", None))
        self.btn_abort.setObjectName(QCoreApplication.translate("MainWindow", u"btn_abort", None))
        self.btn_connect_all.setText(QCoreApplication.translate("MainWindow", u"Connect HW", None))
        self.btn_emergency.setText(QCoreApplication.translate("MainWindow", u"EMERGENCY STOP", None))
        self.btn_emergency.setObjectName(QCoreApplication.translate("MainWindow", u"btn_emergency", None))
    # retranslateUi

