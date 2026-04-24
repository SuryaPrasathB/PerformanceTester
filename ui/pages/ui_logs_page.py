# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'logs_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_LogsPage(object):
    def setupUi(self, LogsPage):
        if not LogsPage.objectName():
            LogsPage.setObjectName(u"LogsPage")
        self.verticalLayout = QVBoxLayout(LogsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame_logs = QFrame(LogsPage)
        self.frame_logs.setObjectName(u"frame_logs")
        self.verticalLayout_logs = QVBoxLayout(self.frame_logs)
        self.verticalLayout_logs.setSpacing(10)
        self.verticalLayout_logs.setObjectName(u"verticalLayout_logs")
        self.verticalLayout_logs.setContentsMargins(15, 15, 15, 15)
        self.lbl_logs_title = QLabel(self.frame_logs)
        self.lbl_logs_title.setObjectName(u"lbl_logs_title")

        self.verticalLayout_logs.addWidget(self.lbl_logs_title)

        self.txt_logs = QTextEdit(self.frame_logs)
        self.txt_logs.setObjectName(u"txt_logs")
        self.txt_logs.setReadOnly(True)

        self.verticalLayout_logs.addWidget(self.txt_logs)


        self.verticalLayout.addWidget(self.frame_logs)


        self.retranslateUi(LogsPage)

        QMetaObject.connectSlotsByName(LogsPage)
    # setupUi

    def retranslateUi(self, LogsPage):
        self.lbl_logs_title.setText(QCoreApplication.translate("LogsPage", u"System Logs & Reports", None))
        pass
    # retranslateUi

