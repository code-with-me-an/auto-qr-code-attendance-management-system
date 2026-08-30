from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

from qr_or_id_generation import student_id_generation

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    "mysql+pymysql",
    username="root",
    password=os.getenv("DB_password"),
    host="localhost",
    port=3306,
    database="aakrithi_attendance",
)
app.config["SQLALCHEMY_TRACk_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20), nullable=False)

    attendances = db.relationship("Attendance", back_populates="student")


class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    attendances = db.relationship("Attendance", back_populates="event")


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.String(20), db.ForeignKey("students.student_id"), nullable=False
    )
    event_id = db.Column(db.Integer, db.ForeignKey("events.event_id"), nullable=False)
    marked_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

    student = db.relationship("Student", back_populates="attendances")
    event = db.relationship("Event", back_populates="attendances")

    __table_args__ = (
        db.UniqueConstraint("student_id", "event_id", name="unique_student_event"),
    )


with app.app_context():
    db.create_all()
    # new_student = Attendance(
    #         student_id = 'AAK030',
    #         event_id = 1,
    #     )
    # db.session.add(new_student)
    # db.session.commit()
    # print(Student.query.all())


@app.route("/")
def dashboard():
    total_students = Student.query.count()
    total_events = Event.query.count()
    total_attendance = Attendance.query.count()

    today = date.today()

    today_attendance = Attendance.query.filter(
        db.func.date(Attendance.marked_at) == today
    ).all()

    event_statistics = []
    events = Event.query.order_by(Event.event_date.desc()).all()

    for event in events:
        count = Attendance.query.filter_by(event_id=event.event_id).count()

        percentage = 0

        if total_students > 0:
            percentage = round((count / total_students) * 100, 1)
        event_statistics.append(
            {"event": event, "count": count, "percentage": percentage}
        )

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_events=total_events,
        total_attendance=total_attendance,
        today_attendance=today_attendance,
        event_statistics=event_statistics,
    )


@app.route("/system_data")
def system_data():
    students = Student.query.order_by(Student.student_id).all()

    events = Event.query.order_by(Event.event_date.desc()).all()

    return render_template("system_data.html", students=students, events=events)


@app.route("/students/add", methods=["POST"])
def add_student():

    # add another python script call
    last_student = Student.query.order_by(Student.student_id.desc()).first()
    last_id_num = int(last_student.student_id[3:]) + 1

    student_id = student_id_generation("AAK", last_id_num)
    student_name = request.form.get("student_name", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    department = request.form.get("department", "").strip()
    year = request.form.get("year", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    new_student = Student(
        student_id=student_id,
        name=student_name,
        roll_number=roll_number,
        department=department,
        year=year,
        email=email,
        phone=phone,
    )

    db.session.add(new_student)
    db.session.commit()

    return redirect(url_for("system_data"))


@app.route("/event/add", methods=["POST"])
def add_event():
    event_name = request.form.get("event_name", "").strip()
    event_date = request.form.get("event_date", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()

    new_event = Event(
        event_name = event_name,
        event_date = event_date,
        start_time = start_time,
        end_time = end_time
    )

    db.session.add(new_event)
    db.session.commit()

    return redirect(url_for('system_data'))


@app.route("/attendance",methods=["GET","POST"])
def attendance():
    if request.method == 'POST':
        student_id = request.form.get("student_id","").strip().upper()
        event_id = request.form.get("event_id","").strip()


        student = Student.query.filter_by(
            student_id=student_id
        ).first()

        if not student:
            print('student is not registerd')
            return {
                "success":False,
                "type":"error",
                "message":"Student id not found"
            },400

        event = Event.query.filter_by(
            event_id = event_id
        ).first()

        if not event:
            print('event is not registerd')
            return {
                "success":False,
                "type":"error",
                "message":"Event id is not found"
            },400



        existing_attendance = Attendance.query.filter_by(
            student_id = student_id,
            event_id = event_id
        ).first()

        if existing_attendance:
            print('already registerd')
            return {
                "success":False,
                "type":"duplicate",
                "message":"Attendance already marked",
                "student_id":student.student_id,
                "student_name":student.name
            },409

        attendance_record = Attendance(
            student_id = student_id,
            event_id = event_id
        )

        try:
            db.session.add(attendance_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            return {
                "success": False,
                "type": "error",
                "message": "Database error"
            },500
        
        print("attendance marked successfully")
        return {
            "success": True,
            "type": "success",
            "message": "Attendance marked successfully.",
            "student_id": student.student_id,
            "student_name": student.name,
            "event_name": event.event_name
        }
        
    events = Event.query.all()
    return render_template("attendance.html",events=events)


if __name__ == "__main__":

    app.run(debug=True)
