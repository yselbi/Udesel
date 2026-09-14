from ui.loginClass import Ui_LoginPage
from PyQt6.QtCore import QUrl, QTimer
from config.settings import AppConfig
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtGui import QIcon, QPixmap
from config.paths import resource_path

class LoginWindow(Ui_LoginPage):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(400, 600)
        icon = QIcon()
        icon_path = resource_path("icons/app_icon.png")
        icon.addPixmap(QPixmap(icon_path), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)
        self.webview = QWebEngineView()
        self.verticalLayout.addWidget(self.webview)
        self.webview.load(QUrl(AppConfig.UDEMY_BASE_URL))

        self.is_logged_in = False
        self.access_token = None
        self.cookies = {}

        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        cookie_store.cookieAdded.connect(self.on_cookie_added)

    def on_cookie_added(self, cookie):
        cookie_name = cookie.name().data().decode()
        cookie_value = cookie.value().data().decode()

        self.cookies[cookie_name] = cookie_value

        if cookie_name == 'access_token':
            self.access_token = cookie_value
            if not self.is_logged_in:
                self.is_logged_in = True
                QTimer.singleShot(1000, self.close)

    def was_login_successful(self):
        return self.is_logged_in

    def get_access_token(self):
        return self.access_token

    def get_cookies(self):
        return self.cookies
