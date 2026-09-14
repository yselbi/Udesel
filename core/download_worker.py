"""
Download worker — writes:
    <root>/<Course>/<NN. Chapter>/<NN. Lecture>_<quality>.mp4
"""
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from utils.helpers import create_valid_filename
from config.settings import AppConfig


class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int, int, str)   # course-level
    lecture_progress = pyqtSignal(int, str)        # per-file
    status_updated = pyqtSignal(str)
    download_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, course, download_path, session, items):
        super().__init__()
        self.course = course
        self.download_path = Path(download_path).expanduser().resolve()
        self.session = session
        self.items = items
        self.is_running = True
        self.failed_lectures = []
        self.total_lectures = sum(
            1 for it in self.items if it.get("_class") == "lecture"
        )
        self._counter = 0

    # ------------------------------------------------------------------
    def run(self):
        try:
            course_title = self.course.get("title", "Course")
            course_path = self.download_path / create_valid_filename(course_title)
            course_path.mkdir(parents=True, exist_ok=True)
            self.status_updated.emit(f"Save folder: {course_path}")

            chapter_index = 0
            chapter_path = course_path / "00. Uncategorized"
            chapter_path.mkdir(parents=True, exist_ok=True)
            in_chapter = 0

            for item in self.items:
                if not self.is_running:
                    break

                cls = item.get("_class")

                if cls == "chapter":
                    chapter_index += 1
                    in_chapter = 0
                    name = f"{chapter_index:02d}. {item.get('title', '')}"
                    chapter_path = course_path / create_valid_filename(name)
                    chapter_path.mkdir(parents=True, exist_ok=True)
                    self.status_updated.emit(f" {name}")
                    continue

                if cls != "lecture":
                    continue

                in_chapter += 1
                self._counter += 1
                title = item.get("title", f"Lecture_{self._counter}")
                numbered = f"{in_chapter:02d}. {title}"

                self.status_updated.emit(
                    f"{self._counter}/{self.total_lectures}: {title}"
                )
                self.progress_updated.emit(
                    self._counter, self.total_lectures, title
                )
                self.lecture_progress.emit(0, numbered)

                if not self._download_lecture(item, chapter_path, numbered):
                    self.failed_lectures.append(title)

                time.sleep(0.4)

            if not self.is_running:
                self.status_updated.emit("⏹ Download stopped")
                return

            if self.failed_lectures:
                self.error_occurred.emit(
                    f"Finished with {len(self.failed_lectures)} failed lectures"
                )
            else:
                self.download_completed.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    # ------------------------------------------------------------------
    def _download_lecture(self, lecture, folder, title):
        asset = lecture.get("asset") or {}
        streams = (asset.get("stream_urls") or {}).get("Video") or []
        mp4s = [s for s in streams if s.get("type") == "video/mp4" and s.get("file")]

        if not mp4s:
            self.status_updated.emit(f"⚠ No MP4 for: {title}")
            return False

        def label_int(s):
            try:
                return int(s.get("label", "0"))
            except (ValueError, TypeError):
                return 0

        best = max(mp4s, key=label_int)
        return self._download_file(
            best["file"], folder, title, quality=best.get("label", "")
        )

    # ------------------------------------------------------------------
    def _download_file(self, url, folder, filename, quality=""):
        try:
            safe = create_valid_filename(filename)
            if quality:
                safe = f"{safe}_{quality}"
            file_path = folder / f"{safe}.mp4"

            if file_path.exists() and file_path.stat().st_size > 0:
                self.status_updated.emit(f"⏭ Skipping existing: {file_path.name}")
                self.lecture_progress.emit(100, safe)
                return True

            r = self.session.get(url, stream=True, timeout=AppConfig.REQUEST_TIMEOUT)
            if r.status_code != 200:
                self.status_updated.emit(f"⚠ HTTP {r.status_code} for {safe}")
                return False

            total_size = int(r.headers.get("content-length", 0))
            downloaded = 0

            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=AppConfig.CHUNK_SIZE):
                    if not self.is_running:
                        return False
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = int((downloaded / total_size) * 100)
                            self.lecture_progress.emit(pct, safe)

            self.lecture_progress.emit(100, safe)
            return True

        except Exception as e:
            self.status_updated.emit(f"{filename}: {e}")
            return False

    # ------------------------------------------------------------------
    def stop(self):
        self.is_running = False
