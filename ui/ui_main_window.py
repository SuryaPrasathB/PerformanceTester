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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 850)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_root = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_root.setSpacing(0)
        self.horizontalLayout_root.setObjectName(u"horizontalLayout_root")
        self.horizontalLayout_root.setContentsMargins(0, 0, 0, 0)
        self.frame_sidebar = QFrame(self.centralwidget)
        self.frame_sidebar.setObjectName(u"frame_sidebar")
        self.frame_sidebar.setMinimumSize(QSize(70, 0))
        self.frame_sidebar.setMaximumSize(QSize(70, 16777215))
        self.frame_sidebar.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_sidebar = QVBoxLayout(self.frame_sidebar)
        self.verticalLayout_sidebar.setSpacing(15)
        self.verticalLayout_sidebar.setObjectName(u"verticalLayout_sidebar")
        self.verticalLayout_sidebar.setContentsMargins(0, 20, 0, 20)
        self.btn_sidebar_toggle = QPushButton(self.frame_sidebar)
        self.btn_sidebar_toggle.setObjectName(u"btn_sidebar_toggle")
        self.btn_sidebar_toggle.setMinimumSize(QSize(70, 60))
        font = QFont()
        font.setPointSize(20)
        self.btn_sidebar_toggle.setFont(font)

        self.verticalLayout_sidebar.addWidget(self.btn_sidebar_toggle)

        self.nav_item_test = QFrame(self.frame_sidebar)
        self.nav_item_test.setObjectName(u"nav_item_test")
        self.hLayout_test = QHBoxLayout(self.nav_item_test)
        self.hLayout_test.setSpacing(10)
        self.hLayout_test.setObjectName(u"hLayout_test")
        self.hLayout_test.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_test = QPushButton(self.nav_item_test)
        self.btn_nav_test.setObjectName(u"btn_nav_test")
        self.btn_nav_test.setMinimumSize(QSize(50, 50))
        self.btn_nav_test.setMaximumSize(QSize(50, 50))

        self.hLayout_test.addWidget(self.btn_nav_test)

        self.lbl_nav_test = QLabel(self.nav_item_test)
        self.lbl_nav_test.setObjectName(u"lbl_nav_test")

        self.hLayout_test.addWidget(self.lbl_nav_test)


        self.verticalLayout_sidebar.addWidget(self.nav_item_test)

        self.nav_item_logs = QFrame(self.frame_sidebar)
        self.nav_item_logs.setObjectName(u"nav_item_logs")
        self.hLayout_logs = QHBoxLayout(self.nav_item_logs)
        self.hLayout_logs.setSpacing(10)
        self.hLayout_logs.setObjectName(u"hLayout_logs")
        self.hLayout_logs.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_logs = QPushButton(self.nav_item_logs)
        self.btn_nav_logs.setObjectName(u"btn_nav_logs")
        self.btn_nav_logs.setMinimumSize(QSize(50, 50))
        self.btn_nav_logs.setMaximumSize(QSize(50, 50))

        self.hLayout_logs.addWidget(self.btn_nav_logs)

        self.lbl_nav_logs = QLabel(self.nav_item_logs)
        self.lbl_nav_logs.setObjectName(u"lbl_nav_logs")

        self.hLayout_logs.addWidget(self.lbl_nav_logs)


        self.verticalLayout_sidebar.addWidget(self.nav_item_logs)

        self.nav_item_debug = QFrame(self.frame_sidebar)
        self.nav_item_debug.setObjectName(u"nav_item_debug")
        self.hLayout_debug = QHBoxLayout(self.nav_item_debug)
        self.hLayout_debug.setSpacing(10)
        self.hLayout_debug.setObjectName(u"hLayout_debug")
        self.hLayout_debug.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_debug = QPushButton(self.nav_item_debug)
        self.btn_nav_debug.setObjectName(u"btn_nav_debug")
        self.btn_nav_debug.setMinimumSize(QSize(50, 50))
        self.btn_nav_debug.setMaximumSize(QSize(50, 50))

        self.hLayout_debug.addWidget(self.btn_nav_debug)

        self.lbl_nav_debug = QLabel(self.nav_item_debug)
        self.lbl_nav_debug.setObjectName(u"lbl_nav_debug")

        self.hLayout_debug.addWidget(self.lbl_nav_debug)


        self.verticalLayout_sidebar.addWidget(self.nav_item_debug)

        self.nav_item_reports = QFrame(self.frame_sidebar)
        self.nav_item_reports.setObjectName(u"nav_item_reports")
        self.hLayout_reports = QHBoxLayout(self.nav_item_reports)
        self.hLayout_reports.setSpacing(10)
        self.hLayout_reports.setObjectName(u"hLayout_reports")
        self.hLayout_reports.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_reports = QPushButton(self.nav_item_reports)
        self.btn_nav_reports.setObjectName(u"btn_nav_reports")
        self.btn_nav_reports.setMinimumSize(QSize(50, 50))
        self.btn_nav_reports.setMaximumSize(QSize(50, 50))

        self.hLayout_reports.addWidget(self.btn_nav_reports)

        self.lbl_nav_reports = QLabel(self.nav_item_reports)
        self.lbl_nav_reports.setObjectName(u"lbl_nav_reports")

        self.hLayout_reports.addWidget(self.lbl_nav_reports)


        self.verticalLayout_sidebar.addWidget(self.nav_item_reports)

        self.nav_item_config = QFrame(self.frame_sidebar)
        self.nav_item_config.setObjectName(u"nav_item_config")
        self.hLayout_config = QHBoxLayout(self.nav_item_config)
        self.hLayout_config.setSpacing(10)
        self.hLayout_config.setObjectName(u"hLayout_config")
        self.hLayout_config.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_config = QPushButton(self.nav_item_config)
        self.btn_nav_config.setObjectName(u"btn_nav_config")
        self.btn_nav_config.setMinimumSize(QSize(50, 50))
        self.btn_nav_config.setMaximumSize(QSize(50, 50))

        self.hLayout_config.addWidget(self.btn_nav_config)

        self.lbl_nav_config = QLabel(self.nav_item_config)
        self.lbl_nav_config.setObjectName(u"lbl_nav_config")

        self.hLayout_config.addWidget(self.lbl_nav_config)

        self.verticalLayout_sidebar.addWidget(self.nav_item_config)

        self.spacer_sidebar = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_sidebar.addItem(self.spacer_sidebar)

        self.nav_item_settings = QFrame(self.frame_sidebar)
        self.nav_item_settings.setObjectName(u"nav_item_settings")
        self.hLayout_settings = QHBoxLayout(self.nav_item_settings)
        self.hLayout_settings.setSpacing(10)
        self.hLayout_settings.setObjectName(u"hLayout_settings")
        self.hLayout_settings.setContentsMargins(10, 0, 0, 0)
        self.btn_nav_settings = QPushButton(self.nav_item_settings)
        self.btn_nav_settings.setObjectName(u"btn_nav_settings")
        self.btn_nav_settings.setMinimumSize(QSize(50, 50))
        self.btn_nav_settings.setMaximumSize(QSize(50, 50))

        self.hLayout_settings.addWidget(self.btn_nav_settings)

        self.lbl_nav_settings = QLabel(self.nav_item_settings)
        self.lbl_nav_settings.setObjectName(u"lbl_nav_settings")

        self.hLayout_settings.addWidget(self.lbl_nav_settings)


        self.verticalLayout_sidebar.addWidget(self.nav_item_settings)


        self.horizontalLayout_root.addWidget(self.frame_sidebar)

        self.widget_content_area = QWidget(self.centralwidget)
        self.widget_content_area.setObjectName(u"widget_content_area")
        self.verticalLayout_content = QVBoxLayout(self.widget_content_area)
        self.verticalLayout_content.setSpacing(0)
        self.verticalLayout_content.setObjectName(u"verticalLayout_content")
        self.verticalLayout_content.setContentsMargins(20, 20, 20, 20)
        self.frame_top_bar = QFrame(self.widget_content_area)
        self.frame_top_bar.setObjectName(u"frame_top_bar")
        self.frame_top_bar.setMinimumSize(QSize(0, 60))
        self.frame_top_bar.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout_top = QHBoxLayout(self.frame_top_bar)
        self.horizontalLayout_top.setObjectName(u"horizontalLayout_top")
        self.lbl_page_title = QLabel(self.frame_top_bar)
        self.lbl_page_title.setObjectName(u"lbl_page_title")
        font1 = QFont()
        font1.setPointSize(16)
        font1.setBold(True)
        self.lbl_page_title.setFont(font1)

        self.horizontalLayout_top.addWidget(self.lbl_page_title)

        self.spacer_top = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_top.addItem(self.spacer_top)

        self.lbl_hw_status = QLabel(self.frame_top_bar)
        self.lbl_hw_status.setObjectName(u"lbl_hw_status")

        self.horizontalLayout_top.addWidget(self.lbl_hw_status)


        self.verticalLayout_content.addWidget(self.frame_top_bar)

        self.stacked_widget = QStackedWidget(self.widget_content_area)
        self.stacked_widget.setObjectName(u"stacked_widget")
        self.page_test = QWidget()
        self.page_test.setObjectName(u"page_test")
        self.stacked_widget.addWidget(self.page_test)

        self.verticalLayout_content.addWidget(self.stacked_widget)


        self.horizontalLayout_root.addWidget(self.widget_content_area)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.stacked_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Performance Tester", None))
        self.btn_sidebar_toggle.setText(QCoreApplication.translate("MainWindow", u"\u2630", None))
        self.btn_nav_test.setText("")
        self.lbl_nav_test.setText(QCoreApplication.translate("MainWindow", u"Test Dashboard", None))
        self.btn_nav_logs.setText("")
        self.lbl_nav_logs.setText(QCoreApplication.translate("MainWindow", u"System Logs", None))
        self.btn_nav_debug.setText("")
        self.lbl_nav_debug.setText(QCoreApplication.translate("MainWindow", u"Debug Screen", None))
        self.btn_nav_reports.setText("")
        self.lbl_nav_reports.setText(QCoreApplication.translate("MainWindow", u"Reports", None))
        self.btn_nav_config.setText("")
        self.lbl_nav_config.setText(QCoreApplication.translate("MainWindow", u"Test Config", None))
        self.btn_nav_settings.setText("")
        self.lbl_nav_settings.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.lbl_page_title.setText(QCoreApplication.translate("MainWindow", u"Test Dashboard", None))
        self.lbl_hw_status.setText(QCoreApplication.translate("MainWindow", u"HW: OK", None))
    # retranslateUi

