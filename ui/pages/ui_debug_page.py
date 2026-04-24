# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'debug_page.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_DebugPage(object):
    def setupUi(self, DebugPage):
        if not DebugPage.objectName():
            DebugPage.setObjectName(u"DebugPage")
        self.verticalLayout = QVBoxLayout(DebugPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(DebugPage)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)


        self.retranslateUi(DebugPage)

        QMetaObject.connectSlotsByName(DebugPage)
    # setupUi

    def retranslateUi(self, DebugPage):
        self.label.setText(QCoreApplication.translate("DebugPage", u"Debug Screen (Coming Soon)", None))
        pass
    # retranslateUi

