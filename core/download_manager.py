"""
Download manager — queues one course at a time.
"""
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from core.download_worker import DownloadWorker


class DownloadManager(QObject):
    progress_updated = pyqtSignal(int, int, str)
    lecture_progress = pyqtSignal(int, str)
    status_updated = pyqtSignal(str)
    download_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    course_completed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.workers = []
        self.current_index = 0
        self.courses = []
        self.api = None
        self.download_path = None
        self.is_running = False

    # ------------------------------------------------------------------
    def download_courses(self, courses, download_path, api):
        self.courses = courses
        self.download_path = Path(download_path).expanduser().resolve()
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.api = api
        self.current_index = 0
        self.workers = []
        self.is_running = True

        self.status_updated.emit(f"Root folder: {self.download_path}")
        self._download_next()

    # ------------------------------------------------------------------
    def _download_next(self):
        if not self.is_running or self.current_index >= len(self.courses):
            if self.is_running:
                self.download_completed.emit()
            return

        course = self.courses[self.current_index]
        title = course.get("title", "Course")
        course_id = course.get("id")

        if not course_id:
            self.error_occurred.emit(f"No ID for {title}")
            self.current_index += 1
            self._download_next()
            return

        self.status_updated.emit(f"Preparing: {title}")

        try:
            items = self.api.get_course_items(course_id)
        except Exception as e:
            self.error_occurred.emit(f"{title}: {e}")
            self.current_index += 1
            self._download_next()
            return

        if not items:
            self.error_occurred.emit(f"No content for {title}")
            self.current_index += 1
            self._download_next()
            return

        worker = DownloadWorker(course, self.download_path, self.api.session, items)
        worker.progress_updated.connect(self.progress_updated)
        worker.lecture_progress.connect(self.lecture_progress)
        worker.status_updated.connect(self.status_updated)
        worker.download_completed.connect(self._on_course_complete)
        worker.error_occurred.connect(self._on_worker_error)

        self.workers.append(worker)
        worker.start()

    # ------------------------------------------------------------------
    def _on_course_complete(self):
        if self.current_index < len(self.courses):
            title = self.courses[self.current_index].get("title", "Course")
            self.course_completed.emit(title)
        self.current_index += 1
        self._download_next()

    def _on_worker_error(self, error):
        self.error_occurred.emit(error)
        self.current_index += 1
        self._download_next()

    # ------------------------------------------------------------------
    def stop_all(self):
        self.is_running = False
        for w in self.workers:
            if w.isRunning():
                w.stop()
                w.wait()
