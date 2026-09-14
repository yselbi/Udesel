from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt


class CourseItem(QListWidgetItem):
    def __init__(self, course_data):
        super().__init__()
        self.course_data = course_data
        title = course_data.get("title", "Untitled Course")
        self.setText(title)
        self.setToolTip(title)
        self.setData(Qt.ItemDataRole.UserRole, course_data)
