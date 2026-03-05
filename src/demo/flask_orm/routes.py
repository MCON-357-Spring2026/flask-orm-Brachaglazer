from __future__ import annotations

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Student, Grade, Assignment

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return {"status": "ok"}


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
    return jsonify([a.to_dict() for a in rows])


@api.get("/assignments/<int:assignment_id>")
def get_assignment(assignment_id: int):
    a = db.session.get(Assignment, assignment_id)
    if not a:
        return {"error": "not found"}, 404
    return a.to_dict()


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

    s = Student(name=name, email=email)
    db.session.add(s)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "email must be unique"}, 409

    return s.to_dict(), 201


@api.get("/students")
def list_students():
    students = Student.query.order_by(Student.name).all()
    return jsonify([s.to_dict() for s in students])


@api.get("/students/<int:student_id>")
def get_student(student_id: int):
    s = db.session.get(Student, student_id)
    if not s:
        return {"error": "not found"}, 404
    return s.to_dict()


@api.patch("/students/<int:student_id>")
def update_student(student_id: int):
    s = db.session.get(Student, student_id)
    if not s:
        return {"error": "not found"}, 404

    data = request.get_json() or {}
    if "name" in data:
        s.name = data["name"]
    if "email" in data:
        s.email = data["email"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "update failed (possibly duplicate email)"}, 409

    return s.to_dict()


@api.delete("/students/<int:student_id>")
def delete_student(student_id: int):
    s = db.session.get(Student, student_id)
    if not s:
        return {"error": "not found"}, 404

    db.session.delete(s)
    db.session.commit()
    return {}, 204


# ---------------------------
# Grades (nested under students)
# Constraint: one grade per student per assignment
# ---------------------------
@api.post("/students/<int:student_id>/grades")
def add_grade(student_id: int):
    s = db.session.get(Student, student_id)
    if not s:
        return {"error": "student not found"}, 404

    data = request.get_json() or {}
    score = data.get("score")
    assignment_id = data.get("assignment_id")

    if score is None or assignment_id is None:
        return {"error": "score and assignment_id are required"}, 400

    try:
        score_int = int(score)
        assignment_id_int = int(assignment_id)
    except (TypeError, ValueError):
        return {"error": "score and assignment_id must be integers"}, 400

    if score_int < 0:
        return {"error": "score must be >= 0"}, 400

    a = db.session.get(Assignment, assignment_id_int)
    if not a:
        return {"error": "assignment not found"}, 404

    g = Grade(score=score_int, student=s, assignment=a)
    db.session.add(g)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "duplicate grade for this student and assignment"}, 409

    return g.to_dict(), 201


@api.get("/students/<int:student_id>/grades")
def list_grades(student_id: int):
    s = db.session.get(Student, student_id)
    if not s:
        return {"error": "student not found"}, 404

    rows = (
        Grade.query
        .filter_by(student_id=student_id)
        .order_by(Grade.created_at.asc())
        .all()
    )

    # Include assignment info for convenience
    payload = []
    for g in rows:
        d = g.to_dict()
        d["assignment"] = {"id": g.assignment.id, "title": g.assignment.title, "max_points": g.assignment.max_points}
        payload.append(d)

    return jsonify(payload)
