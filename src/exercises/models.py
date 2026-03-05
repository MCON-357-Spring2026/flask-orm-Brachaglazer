from __future__ import annotations

from datetime import datetime
from src.exercises.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    grades = db.relationship("Grade", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email}


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    max_points = db.Column(db.Integer, nullable=False)

    grades = db.relationship("Grade", back_populates="assignment", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "max_points": self.max_points}


class Grade(db.Model):
    __tablename__ = "grades"

    __table_args__ = (
        db.UniqueConstraint("student_id", "assignment_id", name="uq_grade_student_assignment"),
    )

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)

    student = db.relationship("Student", back_populates="grades")
    assignment = db.relationship("Assignment", back_populates="grades")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "student_id": self.student_id,
            "assignment_id": self.assignment_id,
        }

