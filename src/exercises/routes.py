from __future__ import annotations

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Student, Grade, Assignment
from . import exercises as ex

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------
# Students
# ---------------------------
@api.post("/students")
def create_student():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return {"error": "name and email are required"}, 400

    try:
        s = ex.create_student(name, email)
        return s.to_dict(), 201
    except ValueError as e:
        return {"error": str(e)}, 409


@api.get("/students")
def list_students():
    rows = ex.get_all_students()
    return [s.to_dict() for s in rows], 200


@api.get("/students/<int:student_id>")
def get_student(student_id: int):
    s = Student.query.get(student_id)
    if not s:
        return {"error": "student not found"}, 404
    return s.to_dict(), 200


@api.patch("/students/<int:student_id>")
def update_student(student_id: int):
    data = request.get_json() or {}
    new_email = data.get("email")

    if not new_email:
        return {"error": "email is required"}, 400

    try:
        s = ex.update_student_email(student_id, new_email)
        return s.to_dict(), 200
    except LookupError:
        return {"error": "student not found"}, 404
    except ValueError as e:
        return {"error": str(e)}, 409


@api.delete("/students/<int:student_id>")
def delete_student(student_id: int):
    try:
        ex.delete_student(student_id)
        return {"message": "student deleted"}, 204
    except LookupError:
        return {"error": "student not found"}, 404


# ---------------------------
# Assignments
# ---------------------------
@api.post("/assignments")
def create_assignment():
    data = request.get_json() or {}
    title = data.get("title")
    max_points = data.get("max_points")

    if not title or max_points is None:
        return {"error": "title and max_points are required"}, 400

    try:
        max_points_int = int(max_points)
    except (TypeError, ValueError):
        return {"error": "max_points must be an integer"}, 400

    if max_points_int <= 0:
        return {"error": "max_points must be > 0"}, 400

    a = Assignment(title=title, max_points=max_points_int)
    db.session.add(a)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "title must be unique"}, 409

    return a.to_dict(), 201


@api.get("/assignments")
def list_assignments():
    rows = Assignment.query.order_by(Assignment.title).all()
    return [a.to_dict() for a in rows], 200


@api.get("/assignments/<int:assignment_id>")
def get_assignment(assignment_id: int):
    a = Assignment.query.get(assignment_id)
    if not a:
        return {"error": "assignment not found"}, 404
    return a.to_dict(), 200


@api.delete("/assignments/<int:assignment_id>")
def delete_assignment(assignment_id: int):
    a = Assignment.query.get(assignment_id)
    if not a:
        return {"error": "assignment not found"}, 404
    db.session.delete(a)
    db.session.commit()
    return {"message": "assignment deleted"}, 204


# ---------------------------
# Grades
# ---------------------------
@api.post("/grades")
def create_grade():
    data = request.get_json() or {}
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    score = data.get("score")

    if student_id is None or assignment_id is None or score is None:
        return {"error": "student_id, assignment_id, and score are required"}, 400

    try:
        score_int = int(score)
    except (TypeError, ValueError):
        return {"error": "score must be an integer"}, 400

    if score_int < 0:
        return {"error": "score must be >= 0"}, 400

    try:
        g = ex.add_grade(student_id, assignment_id, score_int)
        return g.to_dict(), 201
    except LookupError as e:
        return {"error": str(e)}, 404
    except ValueError as e:
        return {"error": str(e)}, 409


@api.get("/grades")
def list_grades():
    rows = Grade.query.order_by(Grade.created_at.desc()).all()
    return [g.to_dict() for g in rows], 200


@api.get("/grades/<int:grade_id>")
def get_grade(grade_id: int):
    g = Grade.query.get(grade_id)
    if not g:
        return {"error": "grade not found"}, 404
    return g.to_dict(), 200


@api.delete("/grades/<int:grade_id>")
def delete_grade(grade_id: int):
    try:
        ex.delete_grade(grade_id)
        return {"message": "grade deleted"}, 204
    except LookupError:
        return {"error": "grade not found"}, 404


# ---------------------------
# Analytics
# ---------------------------
@api.get("/students/<int:student_id>/average")
def student_average(student_id: int):
    try:
        avg = ex.average_percent(student_id)
        return {"student_id": student_id, "average_percent": round(avg, 2)}, 200
    except LookupError:
        return {"error": "student not found"}, 404


@api.get("/students/<int:student_id>/grades")
def student_grades(student_id: int):
    try:
        grades = ex.get_student_grades(student_id)
        return {"student_id": student_id, "grades": [g.to_dict() for g in grades]}, 200
    except LookupError:
        return {"error": "student not found"}, 404


@api.get("/assignments/<int:assignment_id>/grades")
def assignment_grades(assignment_id: int):
    try:
        grades = ex.get_grades_for_assignment(assignment_id)
        return {"assignment_id": assignment_id, "grades": [g.to_dict() for g in grades]}, 200
    except LookupError:
        return {"error": "assignment not found"}, 404


@api.get("/assignments/<int:assignment_id>/highest-score")
def assignment_highest_score(assignment_id: int):
    try:
        score = ex.highest_score_on_assignment(assignment_id)
        return {"assignment_id": assignment_id, "highest_score": score}, 200
    except LookupError:
        return {"error": "assignment not found"}, 404


@api.get("/assignments/<int:assignment_id>/top-scorer")
def assignment_top_scorer(assignment_id: int):
    try:
        student = ex.top_scorer_on_assignment(assignment_id)
        if not student:
            return {"assignment_id": assignment_id, "top_scorer": None}, 200
        return {"assignment_id": assignment_id, "top_scorer": student.to_dict()}, 200
    except LookupError:
        return {"error": "assignment not found"}, 404


@api.get("/class-average")
def class_average():
    avg = ex.class_average_percent()
    return {"class_average_percent": round(avg, 2)}, 200


@api.get("/stats")
def stats():
    return {
        "total_students": len(ex.get_all_students()),
        "total_assignments": Assignment.query.count(),
        "total_grades": ex.total_student_grade_count(),
        "class_average_percent": round(ex.class_average_percent(), 2),
    }, 200


@api.get("/students/top/above-threshold/<float:threshold>")
def top_students(threshold: float):
    students = ex.students_with_average_above(threshold)
    return {"threshold": threshold, "students": [s.to_dict() for s in students]}, 200


@api.get("/assignments/without-grades")
def assignments_no_grades():
    assignments = ex.assignments_without_grades()
    return {"assignments": [a.to_dict() for a in assignments]}, 200

