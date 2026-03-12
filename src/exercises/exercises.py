"""Exercises: ORM fundamentals.

Implement the TODO functions. Autograder will test them.
"""

from __future__ import annotations

from flask import jsonify
from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from src.exercises.extensions import db
from src.exercises.models import Student, Grade, Assignment


# ===== BASIC CRUD =====

def create_student(name: str, email: str) -> Student:
    """TODO: Create and commit a Student; handle duplicate email.

    If email is duplicate:
      - rollback
      - raise ValueError("duplicate email")
    """
    student = Student(name=name, email=email)
    db.session.add(student)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {"error": "email must be unique"}, 400
    return student.to_dict(), 201

def find_student_by_email(email: str) -> Optional[Student]:
    """TODO: Return Student by email or None."""
    student = Student.query.filter_by(email=email).first()
    return student or None


def add_grade(student_id: int, assignment_id: int, score: int) -> Grade:
    """TODO: Add a Grade for the student+assignment and commit.

    If student doesn't exist: raise LookupError
    If assignment doesn't exist: raise LookupError
    If duplicate grade: raise ValueError("duplicate grade")
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError

    grade = Grade(score=score, student_id=student.id, assignment_id=assignment.id)
    db.session.add(grade)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate grade")
    return grade.to_dict(), 201


def average_percent(student_id: int) -> float:
    """TODO: Return student's average percent across assignments.

    percent per grade = score / assignment.max_points * 100

    If student doesn't exist: raise LookupError
    If student has no grades: return 0.0
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError

    avg_expr = func.avg(Grade.score * 100.0 / Assignment.max_points)
    result = (
        db.session.query(avg_expr)
        .select_from(Grade)
        .join(Assignment, Grade.assignment_id == Assignment.id)
        .filter(Grade.student_id == student_id)
        .scalar()
    )
    return float(result) if result is not None else 0.0
    """
    if not student.grades:
        return 0.0
    rows = db.session.query(Grade.score, Assignment.max_points)\
        .join(Grade, Grade.assignment_id == Assignment.id)\
        .filter(Grade.student_id == student_id)\
        .all()
    percent_per_grade = row.score / row.max_points * 100
    return percent_per_grade
    """


# ===== QUERYING & FILTERING =====

def get_all_students() -> list[Student]:
    """TODO: Return all students in database, ordered by name."""
    students = Student.query.order_by(Student.name).all()
    return jsonify([{"id": s.id, "name": s.name, "email": s.email} for s in students])


def get_assignment_by_title(title: str) -> Optional[Assignment]:
    """TODO: Return assignment by title or None."""
    assignment = Assignment.query.filter_by(title=title).first()
    return assignment or None


def get_student_grades(student_id: int) -> list[Grade]:
    """TODO: Return all grades for a student, ordered by assignment title.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError
    return (
        Grade.query.join(Assignment)
        .filter(Grade.student_id == student.id)
        .order_by(Assignment.title)
        .all()
    )


def get_grades_for_assignment(assignment_id: int) -> list[Grade]:
    """TODO: Return all grades for an assignment, ordered by student name.

    If assignment doesn't exist: raise LookupError
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError

    return (
        Grade.query.join(Student)
        .filter(Grade.assignment_id == assignment.id)
        .order_by(Student.name)
        .all()
    )


# ===== AGGREGATION =====

def total_student_grade_count() -> int:
    """TODO: Return total number of grades in database."""
    return Grade.query.count()


def highest_score_on_assignment(assignment_id: int) -> Optional[int]:
    """TODO: Return the highest score on an assignment, or None if no grades.

    If assignment doesn't exist: raise LookupError
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError
    result = db.session.query(func.max(Grade.score)).filter(Grade.assignment_id == assignment_id)
    return int(result) if result is not None else None



def class_average_percent() -> float:
    """TODO: Return average percent across all students and all assignments.

    percent per grade = score / assignment.max_points * 100
    Return average of all these percents.
    If no grades: return 0.0
    """
    raise NotImplementedError


def student_grade_count(student_id: int) -> int:
    """TODO: Return number of grades for a student.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    return len(student.grades)


# ===== UPDATING & DELETION =====

def update_student_email(student_id: int, new_email: str) -> Student:
    """TODO: Update a student's email and commit.

    If student doesn't exist: raise LookupError
    If new email is duplicate: rollback and raise ValueError("duplicate email")
    Return the updated student.
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError
    if student.email == new_email:
        raise ValueError("duplicate email")
    else:
        student.email = new_email
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return {"id": student.id, "name": student.name, "email": student.email}


def delete_student(student_id: int) -> None:
    """TODO: Delete a student and all their grades; commit.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError
    db.session.delete(student)
    db.session.commit()
    return {}, 204


def delete_grade(grade_id: int) -> None:
    """TODO: Delete a grade by id; commit.

    If grade doesn't exist: raise LookupError
    """
    grade = db.session.get(Grade, grade_id)
    if not grade:
        raise LookupError
    db.session.delete(grade)
    db.session.commit()
    return {}, 204


# ===== FILTERING & FILTERING WITH AGGREGATION =====

def students_with_average_above(threshold: float) -> list[Student]:
    """TODO: Return students whose average percent is above threshold.

    List should be ordered by average percent descending.
    percent per grade = score / assignment.max_points * 100
    """
    my_list = []
    all_students = Student.query.all()
    for entry in all_students:
        student = db.session.get(Student, entry.id)
        if not student:
            raise LookupError

        avg_expr = func.avg(Grade.score * 100.0 / Assignment.max_points)
        result = (
            db.session.query(avg_expr)
            .select_from(Grade)
            .join(Assignment, Grade.assignment_id == Assignment.id)
            .filter(Grade.student_id == entry.id)
            .scalar()
        )
        if result >threshold:
            my_list.append(student)
    return my_list


def assignments_without_grades() -> list[Assignment]:
    """TODO: Return assignments that have no grades yet, ordered by title."""
    all_assignments = Assignment.query.all()
    my_list = []
    for entry in all_assignments:
        if not entry.grades:
            my_list.append(entry)
    return my_list


def top_scorer_on_assignment(assignment_id: int) -> Optional[Student]:
    """TODO: Return the Student with the highest score on an assignment.

    If assignment doesn't exist: raise LookupError
    If no grades on assignment: return None
    If tie (multiple students with same high score): return any one
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError
    if not assignment.grades:
        return None
    cursor = ( db.session.query(Assignment.grade, Grade.score)
                .join(Assignment, Assignment.id == Grade.assignment_id)
                .order_by(Grade.score.desc())
                .all()
            )
    return cursor