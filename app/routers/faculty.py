from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import app.auth as auth
import app.models as models
from app.database import SessionLocal
from app.student_dashboard_data import SCHOOL_NAME, SUBJECTS, build_marks_for_student

router = APIRouter(prefix="/faculty", tags=["faculty"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _build_marks(student: models.Student) -> dict:
    return build_marks_for_student(student.cgpa or 0.0)


def _weekly_attendance(current_attendance: float) -> dict:
    a = max(0.0, min(100.0, current_attendance or 0.0))
    return {
        "Mon": round(max(0, min(100, a - 4)), 1),
        "Tue": round(max(0, min(100, a - 2)), 1),
        "Wed": round(max(0, min(100, a + 1)), 1),
        "Thu": round(max(0, min(100, a)), 1),
        "Fri": round(max(0, min(100, a + 2)), 1),
        "Sat": round(max(0, min(100, a - 1)), 1),
    }


def _time_context() -> dict:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return {
            "greeting": "Good Morning",
            "climate": "fresh morning breeze",
            "quote": "Small lessons today, big dreams tomorrow. 🌸",
        }
    if 12 <= hour < 17:
        return {
            "greeting": "Good Afternoon",
            "climate": "warm sunny mood",
            "quote": "Keep teaching with heart, every child is blooming. ☀️",
        }
    return {
        "greeting": "Good Evening",
        "climate": "cool evening calm",
        "quote": "End the day with kindness, learning grows in calm minds. 🌙",
    }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
async def register_faculty(
    request: Request,
    faculty_id: str | None = Form(None),
    name: str | None = Form(None),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = await request.json()
        faculty_id = faculty_id or payload.get("faculty_id")
        name = name or payload.get("name")
        password = password or payload.get("password")

    faculty_id = (faculty_id or "").strip()
    name = (name or "").strip()
    password = (password or "").strip()

    if not faculty_id or not name or not password:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={"school_name": SCHOOL_NAME, "error_message": "Please enter faculty ID, name, and password."},
                status_code=422,
            )
        raise HTTPException(status_code=422, detail="faculty_id, name and password are required")

    existing = db.query(models.Faculty).filter(models.Faculty.faculty_id == faculty_id).first()
    if existing:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={"school_name": SCHOOL_NAME, "error_message": "Faculty ID already exists. Try a different one."},
                status_code=400,
            )
        raise HTTPException(status_code=400, detail="Faculty already registered")

    faculty = models.Faculty(
        faculty_id=faculty_id,
        name=name,
        password=auth.hash_password(password),
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={
                "school_name": SCHOOL_NAME,
                "success_message": "Faculty registered successfully. Please login now.",
            },
        )
    return {"message": "Faculty registered successfully", "faculty_id": faculty.faculty_id}


@router.post("/login")
async def login_faculty(
    request: Request,
    faculty_id: str | None = Form(None),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = await request.json()
        faculty_id = faculty_id or payload.get("faculty_id")
        password = password or payload.get("password")

    faculty_id = (faculty_id or "").strip()
    password = (password or "").strip()

    if not faculty_id or not password:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={"school_name": SCHOOL_NAME, "error_message": "Please enter faculty ID and password."},
                status_code=422,
            )
        raise HTTPException(status_code=422, detail="faculty_id and password are required")

    faculty = auth.authenticate_faculty(db, faculty_id, password)
    if not faculty:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={
                    "school_name": SCHOOL_NAME,
                    "error_message": "Oops! Invalid credentials. Please check and try again.",
                },
                status_code=400,
            )
        raise HTTPException(status_code=400, detail="Invalid credentials")

    students = db.query(models.Student).order_by(models.Student.roll_no).all()
    dashboard_students = []
    for student in students:
        sc = getattr(student, "student_class", None) or "1"
        sec = getattr(student, "section", None) or "A"
        dashboard_students.append(
            {
                "roll_no": student.roll_no,
                "name": student.name,
                "student_class": sc,
                "section": sec,
                "class_label": f"Class {sc} Sec {sec}",
                "attendance": student.attendance,
                "cgpa": student.cgpa,
                "weekly_attendance": _weekly_attendance(student.attendance),
                "marks": _build_marks(student),
            }
        )

    holidays = [
        {"date": "2026-04-01", "name": "Annual Day"},
        {"date": "2026-04-10", "name": "Ram Navami"},
        {"date": "2026-04-14", "name": "Dr. Ambedkar Jayanti"},
        {"date": "2026-05-01", "name": "Labour Day"},
    ]

    weekday = date.today().strftime("%A")
    teaching_groups = [f"Class {i}{sec}" for i in range(1, 6) for sec in ("A", "B")]
    day_schedule = {
        "Monday": [f"{g} - Maths" for g in teaching_groups[:6]],
        "Tuesday": [f"{g} - Science" for g in teaching_groups[2:8]],
        "Wednesday": [f"{g} - English" for g in teaching_groups[1:7]],
        "Thursday": [f"{g} - Social" for g in teaching_groups[3:9]],
        "Friday": [f"{g} - Computer" for g in teaching_groups[:6]],
        "Saturday": [f"{g} - Revision" for g in teaching_groups[:4]],
        "Sunday": [],
    }
    class_groups = {g: {"students": [], "avg_attendance": 0.0, "avg_cgpa": 0.0} for g in teaching_groups}
    for student in dashboard_students:
        key = f"Class {student['student_class']}{student['section']}"
        if key not in class_groups:
            class_groups[key] = {"students": [], "avg_attendance": 0.0, "avg_cgpa": 0.0}
        class_groups[key]["students"].append(student)
    for group in teaching_groups:
        members = class_groups[group]["students"]
        if members:
            class_groups[group]["avg_attendance"] = round(sum(s["attendance"] for s in members) / len(members), 1)
            class_groups[group]["avg_cgpa"] = round(sum(s["cgpa"] for s in members) / len(members), 2)
    time_context = _time_context()

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request=request,
            name="faculty_dashboard.html",
            context={
                "school_name": SCHOOL_NAME,
                "faculty_name": faculty.name,
                "dashboard_name": "Campus Bloom Board",
                "greeting": time_context["greeting"],
                "climate": time_context["climate"],
                "quote": time_context["quote"],
                "class_name": "Classes 1 to 5",
                "section_name": "A & B",
                "students": dashboard_students,
                "subjects": SUBJECTS,
                "teaching_groups": teaching_groups,
                "class_groups": class_groups,
                "holidays": holidays,
                "weekday": weekday,
                "today_classes": day_schedule.get(weekday, []),
            },
        )

    return {
        "message": "Faculty dashboard data loaded",
        "dashboard_name": "Campus Bloom Board",
        "greeting": time_context["greeting"],
        "climate": time_context["climate"],
        "quote": time_context["quote"],
        "class": "Classes 1 to 5",
        "section": "A & B",
        "students": dashboard_students,
        "teaching_groups": teaching_groups,
        "class_groups": class_groups,
        "holidays": holidays,
        "today_day": weekday,
        "today_classes": day_schedule.get(weekday, []),
    }


@router.put("/students/{roll_no}/performance")
async def update_student_performance(
    roll_no: str,
    request: Request,
    attendance: float | None = Form(None),
    cgpa: float | None = Form(None),
    student_class: str | None = Form(None),
    section: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = await request.json()
        if attendance is None:
            attendance = payload.get("attendance")
        if cgpa is None:
            cgpa = payload.get("cgpa")
        if student_class is None:
            student_class = payload.get("student_class")
        if section is None:
            section = payload.get("section")

    if attendance is None and cgpa is None:
        raise HTTPException(status_code=422, detail="attendance or cgpa is required")

    if student_class is not None:
        student_class = (student_class or "").strip()
    if section is not None:
        section = (section or "").strip().upper()

    student_query = db.query(models.Student).filter(models.Student.roll_no == roll_no)
    if student_class:
        student_query = student_query.filter(models.Student.student_class == student_class)
    if section:
        student_query = student_query.filter(models.Student.section == section)
    student = student_query.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if attendance is not None:
        if attendance < 0 or attendance > 100:
            raise HTTPException(status_code=422, detail="attendance must be between 0 and 100")
        student.attendance = attendance

    if cgpa is not None:
        if cgpa < 0 or cgpa > 10:
            raise HTTPException(status_code=422, detail="cgpa must be between 0 and 10")
        student.cgpa = cgpa

    db.commit()
    db.refresh(student)

    return {
        "message": "Student performance updated",
        "student": {
            "roll_no": student.roll_no,
            "name": student.name,
            "attendance": student.attendance,
            "cgpa": student.cgpa,
        },
    }


@router.post("/upload")
def upload(file: UploadFile = File(...)):
    contents = file.file.read()
    return {"filename": file.filename, "size": len(contents)}