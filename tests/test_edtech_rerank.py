from src.edtech_rerank import Course, SearchRequest, rerank_courses


class StubClient:
    def rerank(self, query, candidates, top_k):
        return [1, 0]


def test_deadline_courses_move_to_front_after_model_order():
    courses = [
        Course("open", "Open course", "General study", "self-paced", 20),
        Course("due", "Due course", "Assessment soon", "cohort", 3),
    ]
    result = rerank_courses(SearchRequest("assessment", "learner", deadline_days=7), courses, StubClient())
    assert [course.course_id for course in result] == ["due", "open"]
