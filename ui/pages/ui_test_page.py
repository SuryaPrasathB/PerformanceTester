# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'test_page.ui'
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
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QVBoxLayout, QWidget)

class Ui_TestPage(object):
    def setupUi(self, TestPage):
        if not TestPage.objectName():
            TestPage.setObjectName(u"TestPage")
        self.verticalLayout_main = QVBoxLayout(TestPage)
        self.verticalLayout_main.setSpacing(16)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.splitter_workspace = QSplitter(TestPage)
        self.splitter_workspace.setObjectName(u"splitter_workspace")
        self.splitter_workspace.setOrientation(Qt.Horizontal)
        self.splitter_workspace.setHandleWidth(12)
        self.frame_sidebar = QFrame(self.splitter_workspace)
        self.frame_sidebar.setObjectName(u"frame_sidebar")
        self.frame_sidebar.setFrameShape(QFrame.StyledPanel)
        self.verticalLayout_sidebar = QVBoxLayout(self.frame_sidebar)
        self.verticalLayout_sidebar.setSpacing(10)
        self.verticalLayout_sidebar.setObjectName(u"verticalLayout_sidebar")
        self.verticalLayout_sidebar.setContentsMargins(15, 15, 15, 15)
        self.lbl_section_title = QLabel(self.frame_sidebar)
        self.lbl_section_title.setObjectName(u"lbl_section_title")

        self.verticalLayout_sidebar.addWidget(self.lbl_section_title)

        self.list_tests = QListWidget(self.frame_sidebar)
        self.list_tests.setObjectName(u"list_tests")

        self.verticalLayout_sidebar.addWidget(self.list_tests)

        self.splitter_workspace.addWidget(self.frame_sidebar)
        self.widget_center_container = QWidget(self.splitter_workspace)
        self.widget_center_container.setObjectName(u"widget_center_container")
        self.verticalLayout_center = QVBoxLayout(self.widget_center_container)
        self.verticalLayout_center.setSpacing(16)
        self.verticalLayout_center.setObjectName(u"verticalLayout_center")
        self.verticalLayout_center.setContentsMargins(0, 0, 0, 0)
        self.frame_instruction = QFrame(self.widget_center_container)
        self.frame_instruction.setObjectName(u"frame_instruction")
        self.frame_instruction.setFrameShape(QFrame.StyledPanel)
        self.verticalLayout_instr = QVBoxLayout(self.frame_instruction)
        self.verticalLayout_instr.setSpacing(12)
        self.verticalLayout_instr.setObjectName(u"verticalLayout_instr")
        self.verticalLayout_instr.setContentsMargins(15, 15, 15, 15)
        self.verticalSpacer_top = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_instr.addItem(self.verticalSpacer_top)

        self.lbl_instruction = QLabel(self.frame_instruction)
        self.lbl_instruction.setObjectName(u"lbl_instruction")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setWordWrap(True)

        self.verticalLayout_instr.addWidget(self.lbl_instruction)

        self.horizontalLayout_input = QHBoxLayout()
        self.horizontalLayout_input.setObjectName(u"horizontalLayout_input")
        self.spacer_input_L = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_input.addItem(self.spacer_input_L)

        self.input_instruction = QLineEdit(self.frame_instruction)
        self.input_instruction.setObjectName(u"input_instruction")
        self.input_instruction.setMinimumSize(QSize(350, 45))

        self.horizontalLayout_input.addWidget(self.input_instruction)

        self.btn_done = QPushButton(self.frame_instruction)
        self.btn_done.setObjectName(u"btn_done")
        self.btn_done.setMinimumSize(QSize(120, 45))

        self.horizontalLayout_input.addWidget(self.btn_done)

        self.spacer_input_R = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_input.addItem(self.spacer_input_R)


        self.verticalLayout_instr.addLayout(self.horizontalLayout_input)

        self.verticalSpacer_bottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_instr.addItem(self.verticalSpacer_bottom)

        self.progress_bar = QProgressBar(self.frame_instruction)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setMinimumSize(QSize(0, 12))
        self.progress_bar.setTextVisible(False)

        self.verticalLayout_instr.addWidget(self.progress_bar)


        self.verticalLayout_center.addWidget(self.frame_instruction)

        self.frame_graphs_container = QFrame(self.widget_center_container)
        self.frame_graphs_container.setObjectName(u"frame_graphs_container")
        self.frame_graphs_container.setMinimumSize(QSize(16777215, 280))
        self.frame_graphs_container.setMaximumSize(QSize(16777215, 280))
        self.frame_graphs_container.setFrameShape(QFrame.StyledPanel)
        self.horizontalLayout_graphs = QHBoxLayout(self.frame_graphs_container)
        self.horizontalLayout_graphs.setSpacing(12)
        self.horizontalLayout_graphs.setObjectName(u"horizontalLayout_graphs")
        self.horizontalLayout_graphs.setContentsMargins(15, 15, 15, 15)
        self.lbl_graphs_placeholder = QLabel(self.frame_graphs_container)
        self.lbl_graphs_placeholder.setObjectName(u"lbl_graphs_placeholder")
        self.lbl_graphs_placeholder.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_graphs.addWidget(self.lbl_graphs_placeholder)


        self.verticalLayout_center.addWidget(self.frame_graphs_container)

        self.splitter_workspace.addWidget(self.widget_center_container)

        self.verticalLayout_main.addWidget(self.splitter_workspace)

        self.frame_footer = QFrame(TestPage)
        self.frame_footer.setObjectName(u"frame_footer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_footer.sizePolicy().hasHeightForWidth())
        self.frame_footer.setSizePolicy(sizePolicy)
        self.horizontalLayout_footer = QHBoxLayout(self.frame_footer)
        self.horizontalLayout_footer.setSpacing(15)
        self.horizontalLayout_footer.setObjectName(u"horizontalLayout_footer")
        self.horizontalLayout_footer.setContentsMargins(15, 15, 15, 15)
        self.btn_start = QPushButton(self.frame_footer)
        self.btn_start.setObjectName(u"btn_start")
        self.btn_start.setMinimumSize(QSize(120, 40))

        self.horizontalLayout_footer.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.frame_footer)
        self.btn_stop.setObjectName(u"btn_stop")
        self.btn_stop.setMinimumSize(QSize(120, 40))

        self.horizontalLayout_footer.addWidget(self.btn_stop)

        self.btn_abort = QPushButton(self.frame_footer)
        self.btn_abort.setObjectName(u"btn_abort")
        self.btn_abort.setMinimumSize(QSize(120, 40))

        self.horizontalLayout_footer.addWidget(self.btn_abort)

        self.spacer_footer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_footer.addItem(self.spacer_footer)

        self.lbl_live_data = QLabel(self.frame_footer)
        self.lbl_live_data.setObjectName(u"lbl_live_data")
        self.lbl_live_data.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_footer.addWidget(self.lbl_live_data)

        self.btn_emergency = QPushButton(self.frame_footer)
        self.btn_emergency.setObjectName(u"btn_emergency")
        self.btn_emergency.setMinimumSize(QSize(180, 40))

        self.horizontalLayout_footer.addWidget(self.btn_emergency)


        self.verticalLayout_main.addWidget(self.frame_footer)


        self.retranslateUi(TestPage)

        QMetaObject.connectSlotsByName(TestPage)
    # setupUi

    def retranslateUi(self, TestPage):
        self.lbl_section_title.setText(QCoreApplication.translate("TestPage", u"Test Suite Selection", None))
        self.lbl_instruction.setText(QCoreApplication.translate("TestPage", u"Select a test suite from the left and press Start to begin.", None))
        self.input_instruction.setPlaceholderText(QCoreApplication.translate("TestPage", u"Awaiting user input...", None))
        self.btn_done.setText(QCoreApplication.translate("TestPage", u"Confirm", None))
        self.lbl_graphs_placeholder.setText(QCoreApplication.translate("TestPage", u"Awaiting waveform capture during test sequence...", None))
        self.lbl_graphs_placeholder.setStyleSheet(QCoreApplication.translate("TestPage", u"color: #94A3B8; font-style: italic; font-size: 14px;", None))
        self.btn_start.setText(QCoreApplication.translate("TestPage", u"\u25b6 Start Test", None))
        self.btn_stop.setText(QCoreApplication.translate("TestPage", u"\u23f8 Pause", None))
        self.btn_abort.setText(QCoreApplication.translate("TestPage", u"\u23f9 Abort", None))
        self.lbl_live_data.setText(QCoreApplication.translate("TestPage", u"STATE: IDLE | V: -- V | I: -- A | PF: --", None))
        self.btn_emergency.setText(QCoreApplication.translate("TestPage", u"\u26a0 EMERGENCY STOP", None))
        pass
    # retranslateUi

