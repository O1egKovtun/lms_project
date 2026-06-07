import pytest
from src.models.course import CourseStatus, DifficultyLevel
from src.utils.exceptions import CourseNotFoundError, LessonNotFoundError


class TestCourseCreation:
    def test_create_course_success(self, course_svc, teacher):
        course = course_svc.create_course(
            title="Курс з Python",
            description="Детальний опис курсу з Python",
            teacher_id=teacher.id,
            category="programming",
        )
        assert course.id > 0
        assert course.title == "Курс з Python"
        assert course.status == CourseStatus.DRAFT

    def test_create_course_trims_title(self, course_svc, teacher):
        course = course_svc.create_course(
            title="  Trimmed Title  ",
            description="Достатньо довкий опис курсу",
            teacher_id=teacher.id,
            category="math",
        )
        assert course.title == "Trimmed Title"

    def test_create_course_short_title_raises(self, course_svc, teacher):
        with pytest.raises(ValueError):
            course_svc.create_course(
                title="AB", description="Достатньо довкий опис курсу",
                teacher_id=teacher.id, category="math",
            )

    def test_create_course_short_description_raises(self, course_svc, teacher):
        with pytest.raises(ValueError):
            course_svc.create_course(
                title="Valid Title", description="Short",
                teacher_id=teacher.id, category="math",
            )

    def test_create_course_negative_max_students_raises(self, course_svc, teacher):
        with pytest.raises(ValueError):
            course_svc.create_course(
                title="Valid Title", description="Достатньо довкий опис",
                teacher_id=teacher.id, category="math", max_students=-1,
            )

    def test_create_course_zero_max_students_raises(self, course_svc, teacher):
        with pytest.raises(ValueError):
            course_svc.create_course(
                title="Valid Title", description="Достатньо довкий опис",
                teacher_id=teacher.id, category="math", max_students=0,
            )

    def test_create_course_with_max_students(self, course_svc, teacher):
        course = course_svc.create_course(
            title="Limited Course", description="Курс з обмеженням місць",
            teacher_id=teacher.id, category="math", max_students=30,
        )
        assert course.max_students == 30

    def test_create_course_no_max_students(self, course_svc, teacher):
        course = course_svc.create_course(
            title="Open Course", description="Курс без обмеження",
            teacher_id=teacher.id, category="math",
        )
        assert course.max_students is None

    def test_create_multiple_courses_unique_ids(self, course_svc, teacher):
        c1 = course_svc.create_course("Course One", "Опис першого курсу",
                                      teacher.id, "math")
        c2 = course_svc.create_course("Course Two", "Опис другого курсу",
                                      teacher.id, "math")
        assert c1.id != c2.id

    def test_create_course_with_difficulty(self, course_svc, teacher):
        course = course_svc.create_course(
            title="Advanced Course", description="Складний курс для досвідчених",
            teacher_id=teacher.id, category="cs",
            difficulty=DifficultyLevel.ADVANCED,
        )
        assert course.difficulty == DifficultyLevel.ADVANCED


class TestCoursePublishing:
    def test_publish_draft_course(self, course_svc, teacher):
        course = course_svc.create_course(
            "Pub Test", "Курс для публікації тест", teacher.id, "cat")
        published = course_svc.publish_course(course.id)
        assert published.status == CourseStatus.PUBLISHED

    def test_publish_nonexistent_course_raises(self, course_svc):
        with pytest.raises(CourseNotFoundError):
            course_svc.publish_course(9999)

    def test_archive_published_course(self, course_svc, teacher):
        course = course_svc.create_course(
            "Archive Test", "Курс для архівування тест", teacher.id, "cat")
        course_svc.publish_course(course.id)
        archived = course_svc.archive_course(course.id)
        assert archived.status == CourseStatus.ARCHIVED

    def test_is_published_returns_true(self, course_svc, published_course):
        assert published_course.is_published()

    def test_draft_not_published(self, course_svc, teacher):
        course = course_svc.create_course(
            "Draft", "Чорновий варіант курсу", teacher.id, "cat")
        assert not course.is_published()

    def test_get_published_courses(self, course_svc, published_course, teacher):
        published = course_svc.get_published_courses()
        assert any(c.id == published_course.id for c in published)

    def test_draft_not_in_published_list(self, course_svc, teacher):
        draft = course_svc.create_course("Draft2", "Чорновий 2 варіант",
                                         teacher.id, "cat")
        published = course_svc.get_published_courses()
        assert not any(c.id == draft.id for c in published)


class TestCourseRetrieval:
    def test_get_course_success(self, course_svc, published_course):
        retrieved = course_svc.get_course(published_course.id)
        assert retrieved.id == published_course.id

    def test_get_nonexistent_course_raises(self, course_svc):
        with pytest.raises(CourseNotFoundError):
            course_svc.get_course(9999)

    def test_get_courses_by_teacher(self, course_svc, teacher):
        c1 = course_svc.create_course("Teacher Course 1", "Курс першого вчителя", teacher.id, "cat")
        c2 = course_svc.create_course("Teacher Course 2", "Курс другого вчителя", teacher.id, "cat")
        courses = course_svc.get_courses_by_teacher(teacher.id)
        ids = [c.id for c in courses]
        assert c1.id in ids and c2.id in ids

    def test_get_courses_by_category(self, course_svc, teacher):
        course_svc.create_course("Cat Course", "Курс з категорії math", teacher.id, "math")
        courses = course_svc.get_courses_by_category("math")
        assert len(courses) >= 1
        assert all(c.category.lower() == "math" for c in courses)

    def test_search_courses_by_title(self, course_svc, teacher):
        course_svc.create_course("Django REST API", "Курс з Django REST",
                                  teacher.id, "web")
        results = course_svc.search_courses("django")
        assert len(results) >= 1

    def test_search_courses_by_description(self, course_svc, teacher):
        course_svc.create_course("Web Course", "Повний курс по FastAPI фреймворку",
                                  teacher.id, "web")
        results = course_svc.search_courses("fastapi")
        assert len(results) >= 1

    def test_search_courses_no_result(self, course_svc):
        results = course_svc.search_courses("xyznonexistent123")
        assert results == []


class TestLessonManagement:
    def test_add_lesson_success(self, course_svc, teacher):
        course = course_svc.create_course(
            "Lesson Test", "Курс для тесту уроків", teacher.id, "cat")
        lesson = course_svc.add_lesson(course.id, "Урок 1", "Контент уроку", order=1)
        assert lesson.id > 0
        assert lesson.title == "Урок 1"
        assert lesson.course_id == course.id

    def test_add_lesson_to_nonexistent_course_raises(self, course_svc):
        with pytest.raises(CourseNotFoundError):
            course_svc.add_lesson(9999, "Урок", "Контент", order=1)

    def test_add_lesson_short_title_raises(self, course_svc, teacher):
        course = course_svc.create_course(
            "Test", "Курс для перевірки", teacher.id, "cat")
        with pytest.raises(ValueError):
            course_svc.add_lesson(course.id, "X", "Content", order=1)

    def test_add_lesson_empty_content_raises(self, course_svc, teacher):
        course = course_svc.create_course(
            "Test", "Курс для перевірки", teacher.id, "cat")
        with pytest.raises(ValueError):
            course_svc.add_lesson(course.id, "Valid Title", "", order=1)

    def test_get_course_lessons_ordered(self, course_svc, teacher):
        course = course_svc.create_course(
            "Ordered", "Упорядкований курс з уроками", teacher.id, "cat")
        course_svc.add_lesson(course.id, "Урок 3", "c3", order=3)
        course_svc.add_lesson(course.id, "Урок 1", "c1", order=1)
        course_svc.add_lesson(course.id, "Урок 2", "c2", order=2)
        lessons = course_svc.get_course_lessons(course.id)
        assert [l.order for l in lessons] == [1, 2, 3]

    def test_get_course_lessons_empty(self, course_svc, teacher):
        course = course_svc.create_course(
            "Empty", "Курс без уроків поки що", teacher.id, "cat")
        assert course_svc.get_course_lessons(course.id) == []

    def test_lesson_added_to_course_ids(self, course_svc, teacher):
        course = course_svc.create_course(
            "LessonIds", "Курс для тесту", teacher.id, "cat")
        lesson = course_svc.add_lesson(course.id, "Урок", "Контент", order=1)
        updated_course = course_svc.get_course(course.id)
        assert lesson.id in updated_course.lesson_ids

    def test_delete_lesson(self, course_svc, teacher):
        course = course_svc.create_course(
            "Delete Test", "Курс для видалення", teacher.id, "cat")
        lesson = course_svc.add_lesson(course.id, "Урок", "Контент", order=1)
        result = course_svc.delete_lesson(lesson.id)
        assert result is True

    def test_delete_nonexistent_lesson_raises(self, course_svc):
        with pytest.raises(LessonNotFoundError):
            course_svc.delete_lesson(9999)

    def test_get_nonexistent_lesson_raises(self, course_svc):
        with pytest.raises(LessonNotFoundError):
            course_svc.get_lesson(9999)


class TestCourseUpdate:
    def test_update_course_title(self, course_svc, published_course):
        updated = course_svc.update_course(published_course.id, title="Новий Заголовок")
        assert updated.title == "Новий Заголовок"

    def test_update_course_category(self, course_svc, published_course):
        updated = course_svc.update_course(published_course.id, category="data-science")
        assert updated.category == "data-science"

    def test_update_nonexistent_course_raises(self, course_svc):
        with pytest.raises(CourseNotFoundError):
            course_svc.update_course(9999, title="new")

    def test_course_has_capacity_no_limit(self, course_svc, published_course):
        assert published_course.has_capacity() is True

    def test_course_has_no_capacity_when_full(self, course_svc, teacher):
        course = course_svc.create_course(
            "Full Course", "Курс з обмеженням місць",
            teacher.id, "cat", max_students=1,
        )
        course.increment_enrollment()
        assert not course.has_capacity()
