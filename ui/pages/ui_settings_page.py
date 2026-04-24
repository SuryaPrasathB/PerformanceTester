# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_page.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_SettingsPage(object):
    def setupUi(self, SettingsPage):
        if not SettingsPage.objectName():
            SettingsPage.setObjectName(u"SettingsPage")
        self.verticalLayout = QVBoxLayout(SettingsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame_settings = QFrame(SettingsPage)
        self.frame_settings.setObjectName(u"frame_settings")
        self.verticalLayout_settings = QVBoxLayout(self.frame_settings)
        self.verticalLayout_settings.setSpacing(20)
        self.verticalLayout_settings.setObjectName(u"verticalLayout_settings")
        self.verticalLayout_settings.setContentsMargins(30, 30, 30, 30)
        self.lbl_settings_title = QLabel(self.frame_settings)
        self.lbl_settings_title.setObjectName(u"lbl_settings_title")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.lbl_settings_title.setFont(font)

        self.verticalLayout_settings.addWidget(self.lbl_settings_title)

        self.frame_appearance = QFrame(self.frame_settings)
        self.frame_appearance.setObjectName(u"frame_appearance")
        self.horizontalLayout = QHBoxLayout(self.frame_appearance)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_theme = QLabel(self.frame_appearance)
        self.lbl_theme.setObjectName(u"lbl_theme")

        self.horizontalLayout.addWidget(self.lbl_theme)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.spacer)

        self.btn_toggle_theme = QPushButton(self.frame_appearance)
        self.btn_toggle_theme.setObjectName(u"btn_toggle_theme")

        self.horizontalLayout.addWidget(self.btn_toggle_theme)


        self.verticalLayout_settings.addWidget(self.frame_appearance)

        self.frame_hardware = QFrame(self.frame_settings)
        self.frame_hardware.setObjectName(u"frame_hardware")
        self.horizontalLayout_2 = QHBoxLayout(self.frame_hardware)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lbl_hardware = QLabel(self.frame_hardware)
        self.lbl_hardware.setObjectName(u"lbl_hardware")

        self.horizontalLayout_2.addWidget(self.lbl_hardware)

        self.spacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.spacer_2)

        self.btn_connect_all = QPushButton(self.frame_hardware)
        self.btn_connect_all.setObjectName(u"btn_connect_all")

        self.horizontalLayout_2.addWidget(self.btn_connect_all)


        self.verticalLayout_settings.addWidget(self.frame_hardware)

        self.spacer_bottom = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_settings.addItem(self.spacer_bottom)


        self.verticalLayout.addWidget(self.frame_settings)


        self.retranslateUi(SettingsPage)

        QMetaObject.connectSlotsByName(SettingsPage)
    # setupUi

    def retranslateUi(self, SettingsPage):
        self.lbl_settings_title.setText(QCoreApplication.translate("SettingsPage", u"Application Settings", None))
        self.lbl_theme.setText(QCoreApplication.translate("SettingsPage", u"Display Theme", None))
        self.btn_toggle_theme.setText(QCoreApplication.translate("SettingsPage", u"Switch to Dark/Light", None))
        self.lbl_hardware.setText(QCoreApplication.translate("SettingsPage", u"Hardware Connectivity", None))
        self.btn_connect_all.setText(QCoreApplication.translate("SettingsPage", u"Connect All HW", None))
        pass
    # retranslateUi

