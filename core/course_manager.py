import requests


class CourseManager:
    def __init__(self, session: requests.Session):
        self.session = session
        self.courses = []

    # ------------------------------------------------------------------
    def fetch_courses(self):
        try:
            r = self.session.get(
                "https://www.udemy.com/api-2.0/users/me/subscribed-courses/",
                params={"page_size": 100},
            )
            if r.status_code != 200:
                return []
            self.courses = r.json().get("results", [])
            return self.courses
        except Exception as e:
            print(f"fetch_courses error: {e}")
            return []

    # ------------------------------------------------------------------
    def fetch_curriculum(self, course_id):
        url = (
            f"https://www.udemy.com/api-2.0/courses/"
            f"{course_id}/cached-subscriber-curriculum-items"
        )
        params = {
            "page_size": 100000,
            "fields[asset]": (
                "results,external_url,time_estimation,download_urls,"
                "slide_urls,filename,asset_type,captions,stream_urls,body"
            ),
            "fields[chapter]": "object_index,title,sort_order",
            "fields[lecture]": "id,title,object_index,asset,supplementary_assets,view_html",
        }
        try:
            r = self.session.get(url, params=params)
            print(f"curriculum {course_id}: HTTP {r.status_code}")
            if r.status_code != 200:
                return None
            return r.json()
        except Exception as e:
            print(f"fetch_curriculum error: {e}")
            return None

    # ------------------------------------------------------------------
    def get_course_items(self, course_id):
        """Raw flat list (chapters + lectures + quizzes) for the downloader."""
        data = self.fetch_curriculum(course_id)
        if not data:
            return []
        return data.get("results", [])
