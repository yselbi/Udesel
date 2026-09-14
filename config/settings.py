"""
Application settings and constants
"""
from pathlib import Path
from config.paths import resource_path

class AppConfig:
    APP_NAME = "Udesel"
    APP_VERSION = "v1.0.0"
    APP_AUTHOR = "Yahya SELBI"
    APP_ICON = resource_path("icons/app_icon.png")

    # Default paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DOWNLOADS_DIR = Path.home() / "Downloads" / "Udemy_Courses"
    LOGS_DIR = BASE_DIR / "logs"

    # API settings
    UDEMY_BASE_URL = "https://www.udemy.com/join/passwordless-auth/"


    # Download settings
    CHUNK_SIZE = 8192
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    REQUEST_TIMEOUT = 30  # seconds

    # UI settings
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 700
    WINDOW_DEFAULT_WIDTH = 1200
    WINDOW_DEFAULT_HEIGHT = 800
    SPLITTER_SIZES = [500, 700]

    # Logging
    LOG_MAX_LINES = 1000
    LOG_DATE_FORMAT = "%H:%M:%S"


class Settings:
    @staticmethod
    def get_download_path():
        return AppConfig.DOWNLOADS_DIR

    @staticmethod
    def set_download_path(path):
        AppConfig.DOWNLOADS_DIR = Path(path)

    @staticmethod
    def ensure_directories():
        AppConfig.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        AppConfig.LOGS_DIR.mkdir(parents=True, exist_ok=True)
