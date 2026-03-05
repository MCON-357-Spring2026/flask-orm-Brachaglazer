"""Demo: Flask ORM without running a server.

Run:
  python -m src.demo.demo
"""

from src.demo.flask_orm.app import create_app
from src.demo.flask_orm.extensions import db
from src.demo.flask_orm.models import Student, Grade, Assignment


def main() -> None:
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        a1 = Assignment(title="Quiz 1", max_points=10)
        db.session.add(a1)

        ava = Student(name="Ava", email="ava@example.com")
        db.session.add(ava)
        db.session.commit()

        db.session.add_all([
            Grade(score=9, student=ava, assignment=a1),
        ])
        db.session.commit()

        print("Students:", [s.to_dict() for s in Student.query.all()])
        print("Assignments:", [a.to_dict() for a in Assignment.query.all()])
        print("Grades:", [g.to_dict() for g in Grade.query.all()])


if __name__ == "__main__":
    main()
