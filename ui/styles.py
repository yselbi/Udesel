class AppStyles:
    MAIN_STYLE = """
    QMainWindow { background: #f7f9fc; }
    QGroupBox {
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        margin-top: 10px;
        padding: 8px;
        font-weight: bold;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
    QPushButton {
        padding: 6px 12px;
        border: 1px solid #b9c4d2;
        border-radius: 4px;
        background: #ffffff;
    }
    QPushButton:hover { background: #eef3f8; }
    QPushButton:disabled { color: #9aa5b1; background: #f0f0f0; }
    QListWidget { background: #ffffff; border: 1px solid #cfd8e3; border-radius: 4px; }
    QTextBrowser { background: #ffffff; border: 1px solid #cfd8e3; border-radius: 4px; }
    """
