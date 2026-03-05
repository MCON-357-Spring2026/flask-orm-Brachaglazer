import pytest

from src.demo.flask_orm.app import create_app
from src.demo.flask_orm.extensions import db
from src.demo.flask_orm.models import Assignment, Student, Grade
from src.exercises import exercises as ex


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ===== BASIC CRUD TESTS =====

def test_create_student(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        assert s.name == "Alice"
        assert s.email == "alice@example.com"
        assert s.id is not None


def test_create_student_duplicate_email(app):
    with app.app_context():
        ex.create_student("Alice", "alice@example.com")
        with pytest.raises(ValueError):
            ex.create_student("Bob", "alice@example.com")


def test_find_student_by_email(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        found = ex.find_student_by_email("alice@example.com")
        assert found.id == s.id
        assert found.name == "Alice"


def test_find_student_by_email_not_found(app):
    with app.app_context():
        result = ex.find_student_by_email("notfound@example.com")
        assert result is None


def test_add_grade(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        g = ex.add_grade(s.id, a.id, 9)
        assert g.score == 9
        assert g.student_id == s.id
        assert g.assignment_id == a.id


def test_add_grade_duplicate(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s.id, a.id, 9)
        with pytest.raises(ValueError):
            ex.add_grade(s.id, a.id, 10)


def test_add_grade_missing_student(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        with pytest.raises(LookupError):
            ex.add_grade(999, a.id, 9)


def test_add_grade_missing_assignment(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        with pytest.raises(LookupError):
            ex.add_grade(s.id, 999, 9)


def test_average_percent(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s.id, a1.id, 9)    # 90%
        ex.add_grade(s.id, a2.id, 95)   # 95%
        assert round(ex.average_percent(s.id), 1) == 92.5


def test_average_percent_no_grades(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        assert ex.average_percent(s.id) == 0.0


def test_average_percent_missing_student(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.average_percent(999)


# ===== QUERYING & FILTERING TESTS =====

def test_get_all_students(app):
    with app.app_context():
        s1 = ex.create_student("Charlie", "charlie@example.com")
        s2 = ex.create_student("Alice", "alice@example.com")
        s3 = ex.create_student("Bob", "bob@example.com")

        students = ex.get_all_students()
        assert len(students) == 3
        assert students[0].name == "Alice"  # ordered by name
        assert students[1].name == "Bob"
        assert students[2].name == "Charlie"


def test_get_assignment_by_title(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        found = ex.get_assignment_by_title("Quiz 1")
        assert found.id == a.id


def test_get_assignment_by_title_not_found(app):
    with app.app_context():
        result = ex.get_assignment_by_title("Missing")
        assert result is None


def test_get_student_grades(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s.id, a2.id, 95)
        ex.add_grade(s.id, a1.id, 9)

        grades = ex.get_student_grades(s.id)
        assert len(grades) == 2
        assert grades[0].assignment.title == "HW 1"  # ordered by assignment title
        assert grades[1].assignment.title == "Quiz 1"


def test_get_student_grades_missing_student(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.get_student_grades(999)


def test_get_grades_for_assignment(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s1 = ex.create_student("Charlie", "charlie@example.com")
        s2 = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s1.id, a.id, 9)
        ex.add_grade(s2.id, a.id, 10)

        grades = ex.get_grades_for_assignment(a.id)
        assert len(grades) == 2
        assert grades[0].student.name == "Alice"  # ordered by student name
        assert grades[1].student.name == "Charlie"


def test_get_grades_for_assignment_missing_assignment(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.get_grades_for_assignment(999)


# ===== AGGREGATION TESTS =====

def test_total_student_grade_count(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        ex.add_grade(s1.id, a1.id, 9)
        ex.add_grade(s1.id, a2.id, 95)
        ex.add_grade(s2.id, a1.id, 8)

        assert ex.total_student_grade_count() == 3


def test_total_student_grade_count_empty(app):
    with app.app_context():
        assert ex.total_student_grade_count() == 0


def test_highest_score_on_assignment(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        ex.add_grade(s1.id, a.id, 9)
        ex.add_grade(s2.id, a.id, 10)

        assert ex.highest_score_on_assignment(a.id) == 10


def test_highest_score_on_assignment_no_grades(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        assert ex.highest_score_on_assignment(a.id) is None


def test_highest_score_on_assignment_missing(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.highest_score_on_assignment(999)


def test_class_average_percent(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        ex.add_grade(s1.id, a1.id, 10)  # 100%
        ex.add_grade(s1.id, a2.id, 100)  # 100%
        ex.add_grade(s2.id, a1.id, 5)  # 50%
        ex.add_grade(s2.id, a2.id, 50)  # 50%

        assert ex.class_average_percent() == 75.0


def test_class_average_percent_no_grades(app):
    with app.app_context():
        assert ex.class_average_percent() == 0.0


def test_student_grade_count(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s.id, a1.id, 9)
        ex.add_grade(s.id, a2.id, 95)

        assert ex.student_grade_count(s.id) == 2


def test_student_grade_count_missing_student(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.student_grade_count(999)


# ===== UPDATING & DELETION TESTS =====

def test_update_student_email(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        updated = ex.update_student_email(s.id, "alice.new@example.com")
        assert updated.email == "alice.new@example.com"
        assert ex.find_student_by_email("alice.new@example.com").id == s.id


def test_update_student_email_missing_student(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.update_student_email(999, "new@example.com")


def test_update_student_email_duplicate(app):
    with app.app_context():
        ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        with pytest.raises(ValueError):
            ex.update_student_email(s2.id, "alice@example.com")


def test_delete_student(app):
    with app.app_context():
        s = ex.create_student("Alice", "alice@example.com")
        ex.delete_student(s.id)
        assert ex.find_student_by_email("alice@example.com") is None


def test_delete_student_missing(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.delete_student(999)


def test_delete_student_cascades_grades(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        g = ex.add_grade(s.id, a.id, 9)
        grade_id = g.id

        ex.delete_student(s.id)
        assert Grade.query.get(grade_id) is None


def test_delete_grade(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        g = ex.add_grade(s.id, a.id, 9)
        grade_id = g.id

        ex.delete_grade(grade_id)
        assert Grade.query.get(grade_id) is None


def test_delete_grade_missing(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.delete_grade(999)


# ===== ADVANCED FILTERING TESTS =====

def test_students_with_average_above(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        db.session.add_all([a1, a2])
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        s3 = ex.create_student("Charlie", "charlie@example.com")

        ex.add_grade(s1.id, a1.id, 10)  # 100%
        ex.add_grade(s1.id, a2.id, 100)  # 100% -> avg 100%

        ex.add_grade(s2.id, a1.id, 9)  # 90%
        ex.add_grade(s2.id, a2.id, 90)  # 90% -> avg 90%

        ex.add_grade(s3.id, a1.id, 5)  # 50%
        ex.add_grade(s3.id, a2.id, 50)  # 50% -> avg 50%

        above_90 = ex.students_with_average_above(90.0)
        assert len(above_90) == 1
        assert above_90[0].name == "Alice"


def test_students_with_average_above_ordered(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")

        ex.add_grade(s1.id, a.id, 8)  # 80%
        ex.add_grade(s2.id, a.id, 9)  # 90%

        above_70 = ex.students_with_average_above(70.0)
        assert len(above_70) == 2
        assert above_70[0].name == "Bob"  # Higher average first
        assert above_70[1].name == "Alice"


def test_assignments_without_grades(app):
    with app.app_context():
        a1 = Assignment(title="Quiz 1", max_points=10)
        a2 = Assignment(title="HW 1", max_points=100)
        a3 = Assignment(title="Final", max_points=50)
        db.session.add_all([a1, a2, a3])
        db.session.commit()

        s = ex.create_student("Alice", "alice@example.com")
        ex.add_grade(s.id, a1.id, 9)

        no_grades = ex.assignments_without_grades()
        assert len(no_grades) == 2
        assert no_grades[0].title == "Final"  # ordered by title
        assert no_grades[1].title == "HW 1"


def test_top_scorer_on_assignment(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        s1 = ex.create_student("Alice", "alice@example.com")
        s2 = ex.create_student("Bob", "bob@example.com")
        ex.add_grade(s1.id, a.id, 9)
        ex.add_grade(s2.id, a.id, 10)

        top = ex.top_scorer_on_assignment(a.id)
        assert top.name == "Bob"


def test_top_scorer_on_assignment_no_grades(app):
    with app.app_context():
        a = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a)
        db.session.commit()

        result = ex.top_scorer_on_assignment(a.id)
        assert result is None


def test_top_scorer_on_assignment_missing(app):
    with app.app_context():
        with pytest.raises(LookupError):
            ex.top_scorer_on_assignment(999)

