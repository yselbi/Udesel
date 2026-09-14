
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget

class Ui_LoginPage(QWidget):
    def __init__(self):
        super().__init__()
    def setupUi(self, LoginPage):
        LoginPage.setObjectName("LoginPage")
        LoginPage.resize(689, 428)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(".\\ui\\../icons/app_icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        LoginPage.setWindowIcon(icon)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(LoginPage)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(LoginPage)
        QtCore.QMetaObject.connectSlotsByName(LoginPage)

    def retranslateUi(self, LoginPage):
        _translate = QtCore.QCoreApplication.translate
        LoginPage.setWindowTitle(_translate("LoginPage", "Udesel - Udemy Login"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    LoginPage = QtWidgets.QWidget()
    ui = Ui_LoginPage()
    ui.setupUi(LoginPage)
    LoginPage.show()
    sys.exit(app.exec())
