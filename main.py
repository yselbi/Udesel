"""
APP_NAME = "Udesel"
APP_VERSION = "v1.0.0"
APP_AUTHOR = "Yahya SELBI"
APP_ICON = "icons/window_icon.png"
Date Created : September - 2026
"""





import sys
import os
import html as _html
import requests
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap

from ui.mainClass import Ui_MainWindow
from ui.styles import AppStyles
from ui.loginWindow import LoginWindow
from ui.course_item import CourseItem
from config.settings import AppConfig, Settings
from core.course_manager import CourseManager
from core.download_manager import DownloadManager
from config.paths import resource_path

class MainWindow(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        icon = QIcon()
        icon_path = resource_path("icons/app_icon.png")
        icon.addPixmap(QPixmap(icon_path), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)
        self.setStyleSheet(AppStyles.MAIN_STYLE)
        self.setWindowTitle(f"{AppConfig.APP_NAME} {AppConfig.APP_VERSION} — by {AppConfig.APP_AUTHOR}")
        self.setMinimumSize(AppConfig.WINDOW_MIN_WIDTH, AppConfig.WINDOW_MIN_HEIGHT)
        self.resize(AppConfig.WINDOW_DEFAULT_WIDTH, AppConfig.WINDOW_DEFAULT_HEIGHT)

        self.access_token = None
        self.session = None
        self.course_manager = None
        self.courses = []
        self.current_curriculum = None

        self.download_manager = DownloadManager()
        self.download_manager.progress_updated.connect(self.on_progress)
        self.download_manager.lecture_progress.connect(self.on_lecture_progress)
        self.download_manager.status_updated.connect(self.on_status)
        self.download_manager.error_occurred.connect(self.on_error)
        self.download_manager.download_completed.connect(self.on_all_done)
        self.download_manager.course_completed.connect(self.on_course_done)

        self.course_list.itemClicked.connect(self.show_course_details)
        self.path_button.clicked.connect(self.browse_download_path)
        self.download_btn.clicked.connect(self.start_download)
        self.stop_btn.clicked.connect(self.download_manager.stop_all)
        self.search_input.textChanged.connect(self.filter_courses)
        self.refresh_btn.clicked.connect(self.refresh_courses)
        self.logout_btn.clicked.connect(self.logout)

        self.course_details.setAcceptRichText(True)
        self.course_details.setOpenExternalLinks(True)

        self.path_input.setText(str(AppConfig.DOWNLOADS_DIR))

        self.menuAbout.triggered.connect(self.show_about)

    # ==================================================================
    # Login
    # ==================================================================
    def open_login_page(self):
        login = LoginWindow()
        login.show()
        while login.isVisible():
            QApplication.processEvents()

        if not login.was_login_successful():
            return False
        self.access_token = login.get_access_token()

        self.session = requests.Session()
        for name, value in login.get_cookies().items():
            self.session.cookies.set(name, value)
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

        self.course_manager = CourseManager(self.session)

        try:
            r = self.session.get("https://www.udemy.com/api-2.0/users/me/")
            if r.status_code == 200:
                user = r.json()
                name = (
                    user.get("display_name")
                    or user.get("title")
                    or user.get("name")
                    or "Unknown"
                )
                self.user_label.setText(f"👤 {name}")
                self.load_courses()
            else:
                self.user_label.setText("Not logged in")
        except Exception as e:
            self.user_label.setText("Not logged in")

        self.show()
        return True

    def logout(self):
        self.session = None
        self.course_manager = None
        self.access_token = None
        self.courses = []
        self.current_curriculum = None
        self.course_list.clear()
        self.course_details.clear()
        self.user_label.setText("Not logged in")
        self.download_btn.setEnabled(False)
        self.close()

    # ==================================================================
    # Course list
    # ==================================================================
    def load_courses(self):
        if not self.course_manager:
            return
        self.courses = self.course_manager.fetch_courses()
        self.course_list.clear()
        for course in self.courses:
            self.course_list.addItem(CourseItem(course))


    def refresh_courses(self):
        if not self.course_manager:
            return
        self.load_courses()

    def filter_courses(self, text):
        text = text.lower()
        for i in range(self.course_list.count()):
            item = self.course_list.item(i)
            item.setHidden(text not in item.text().lower())

    # ==================================================================
    # Curriculum rendering
    # ==================================================================
    @staticmethod
    def _group_curriculum(data):
        sections, current = [], None
        for item in data.get("results", []):
            cls = item.get("_class")
            if cls == "chapter":
                current = {"title": item.get("title", ""), "items": []}
                sections.append(current)
            elif cls in ("lecture", "quiz", "practice"):
                if current is None:
                    current = {"title": "—", "items": []}
                    sections.append(current)
                current["items"].append(item)
        return sections

    @staticmethod
    def _best_mp4(asset):
        streams = (asset.get("stream_urls") or {}).get("Video") or []
        mp4s = [s for s in streams if s.get("type") == "video/mp4" and s.get("file")]
        if not mp4s:
            return None

        def label_int(s):
            try:
                return int(s.get("label", "0"))
            except (ValueError, TypeError):
                return 0

        return max(mp4s, key=label_int)

    def _render_curriculum(self, data):
        sections = self._group_curriculum(data)
        n_lec = sum(1 for s in sections for i in s["items"] if i["_class"] == "lecture")
        n_qz = sum(1 for s in sections for i in s["items"] if i["_class"] == "quiz")
        n_min = sum(
            (i.get("asset") or {}).get("time_estimation", 0) or 0
            for s in sections for i in s["items"]
        )

        html = [
            "<hr>",
            f"<p style='color:#666;margin:6px 0;'>"
            f"{len(sections)} sections · {n_lec} lectures · {n_qz} quizzes · "
            f"{n_min // 60}h {n_min % 60}m</p>",
        ]

        for i, sec in enumerate(sections, 1):
            html.append(
                f"<h3 style='background:#eef3f8;padding:6px 10px;"
                f"border-radius:4px;margin:16px 0 8px 0;'>"
                f"§{i}. {_html.escape(sec['title'])} "
                f"<span style='color:#888;font-weight:normal;font-size:11px;'>"
                f"({len(sec['items'])} items)</span></h3>"
            )
            for it in sec["items"]:
                cls = it["_class"]
                title = _html.escape(it.get("title", ""))

                if cls == "lecture":
                    asset = it.get("asset") or {}
                    secs = asset.get("time_estimation", 0) or 0
                    dur = (
                        f" <span style='color:#888;'>— "
                        f"{secs // 60}:{secs % 60:02d}</span>" if secs else ""
                    )
                    best = self._best_mp4(asset)
                    dl = (
                        f'<span style="color:#2c7a3f;">⬇ {best["label"]}p</span>'
                        if best else
                        "<span style='color:#c00;'>no video</span>"
                    )
                    atts = []
                    for a in it.get("supplementary_assets") or []:
                        for d in (a.get("download_urls") or {}).get("File", []):
                            atts.append(f'📎 {_html.escape(a.get("filename", "file"))}')

                    row = (
                        f"<p style='margin:6px 0 6px 18px;'>"
                        f"🎬 <b>{title}</b>{dur}<br>"
                        f"<span style='margin-left:18px;'>{dl}</span>"
                    )
                    if atts:
                        row += (
                            "<br><span style='margin-left:18px;font-size:11px;"
                            "color:#666;'>" + "<br>".join(atts) + "</span>"
                        )
                    row += "</p>"
                    html.append(row)

                elif cls == "quiz":
                    html.append(
                        f"<p style='margin:4px 0 4px 18px;color:#8a6d3b;'>"
                        f" <i>{title}</i></p>"
                    )
                else:
                    html.append(f"<p style='margin:4px 0 4px 18px;'> {title}</p>")

        self.course_details.append("".join(html))

    # ==================================================================
    # Course click
    # ==================================================================
    def show_course_details(self, item):
        index = self.course_list.row(item)
        if not (0 <= index < len(self.courses)):
            return

        course = self.courses[index]
        cid = course.get("id")
        title = course.get("title", "Untitled")
        url = course.get("url", "")
        instructors = course.get("visible_instructors", [])
        names = ", ".join(i.get("name", "") for i in instructors if i.get("name"))

        header = [f"<h1 style='margin:0;'>{_html.escape(title)}</h1>"]
        meta = []
        if names:
            meta.append(f"👤 {_html.escape(names)}")
        meta.append(f"<span style='color:#666;'>ID: {cid}</span>")
        if url:
            meta.append(f'<a href="https://www.udemy.com{url}"> Course page</a>')
        header.append("<p style='margin:4px 0;'>" + " &nbsp;·&nbsp; ".join(meta) + "</p>")

        self.course_details.setHtml("".join(header))
        self.course_details.append("<p style='color:#888;'> Loading curriculum…</p>")
        QApplication.processEvents()

        data = self.course_manager.fetch_curriculum(cid)
        if not data or not data.get("results"):
            self.course_details.append("<p style='color:red;'>No curriculum returned.</p>")
            self.download_btn.setEnabled(False)
            return

        self.current_curriculum = data
        self.course_details.setHtml("".join(header))
        self._render_curriculum(data)
        self.download_btn.setEnabled(True)

    # ==================================================================
    # Download
    # ==================================================================
    def browse_download_path(self):
        start = self.path_input.text() or str(AppConfig.DOWNLOADS_DIR)
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder", start)
        if folder:
            self.path_input.setText(folder)

    def start_download(self):
        items = self.course_list.selectedItems()
        if not items:
            return
        index = self.course_list.row(items[0])
        if not (0 <= index < len(self.courses)):
            return

        course = self.courses[index]
        raw = self.path_input.text().strip() or str(AppConfig.DOWNLOADS_DIR)
        path = os.path.abspath(os.path.expanduser(raw))

        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                print(f"Cannot create folder: {e}")
                return

        self.path_input.setText(path)
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.lecture_progress.setValue(0)
        self.course_progress.setValue(0)

        self.download_manager.download_courses([course], path, self.course_manager)

    # ==================================================================
    # Signal handlers
    # ==================================================================
    def on_progress(self, cur, total, name):
        self.course_progress.setMaximum(total)
        self.course_progress.setValue(cur)

    def on_lecture_progress(self, pct, name):
        self.lecture_progress.setMaximum(100)
        self.lecture_progress.setValue(pct)
        self.current_file_label.setText(name)

    def on_status(self, msg):
        self.status_label.setText(msg)
        print(msg)

    def on_error(self, msg):
        print(f"{msg}")

    def on_course_done(self, title):
        print(f"Finished: {title}")

    def on_all_done(self):
        print("🎉 All downloads finished")
        self.status_label.setText("Done")
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def show_about(self):
        print("ABOUT CLICKED")
        QMessageBox.about(
            self,
            "About",
            f"<h3>{AppConfig.APP_NAME} {AppConfig.APP_VERSION}</h3>"
            f"<p>By <b>{AppConfig.APP_AUTHOR}</b></p>",
        )


# ======================================================================
def main():
    Settings.ensure_directories()
    app = QApplication(sys.argv)
    win = MainWindow()
    if win.open_login_page():
        sys.exit(app.exec())
    sys.exit(0)


if __name__ == "__main__":
    main()
