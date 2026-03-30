from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import app.auth as auth
import app.models as models
from app.database import SessionLocal
from app.student_dashboard_data import (
    SCHOOL_NAME,
    SUBJECTS,
    build_fees_details,
    build_marks_for_student,
    build_timetable,
    profile_initials,
    reference_notes,
)

router = APIRouter(prefix="/students", tags=["students"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
async def register_student(
    request: Request,
    roll_no: str | None = Form(None),
    name: str | None = Form(None),
    password: str | None = Form(None),
    student_class: str | None = Form(None),
    section: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = await request.json()
        roll_no = roll_no or payload.get("roll_no")
        name = name or payload.get("name")
        password = password or payload.get("password")
        student_class = student_class or payload.get("student_class")
        section = section or payload.get("section")

    roll_no = (roll_no or "").strip()
    name = (name or "").strip()
    password = (password or "").strip()
    student_class = (student_class or "1").strip()
    section = (section or "A").strip().upper()
    if section not in ("A", "B"):
        section = "A"
    if student_class not in {str(i) for i in range(1, 6)}:
        student_class = "1"

    if not roll_no or not name or not password:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={"school_name": SCHOOL_NAME, "error_message": "Please enter roll no, name, and password."},
                status_code=422,
            )
        raise HTTPException(status_code=422, detail="roll_no, name and password are required")

    existing = (
        db.query(models.Student)
        .filter(
            models.Student.roll_no == roll_no,
            models.Student.student_class == student_class,
            models.Student.section == section,
        )
        .first()
    )
    if existing:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={
                    "school_name": SCHOOL_NAME,
                    "error_message": "This roll no already exists in this class/section. Try another class/section.",
                },
                status_code=400,
            )
        raise HTTPException(status_code=400, detail="Student already registered")

    student = models.Student(
        roll_no=roll_no,
        name=name,
        password=auth.hash_password(password),
        attendance=0.0,
        cgpa=0.0,
        student_class=student_class,
        section=section,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={
                "school_name": SCHOOL_NAME,
                "success_message": "Student registered successfully. Please login now.",
            },
        )
    return {"message": "Student registered successfully", "roll_no": student.roll_no}


@router.post("/login")
async def login_student(
    request: Request,
    roll_no: str | None = Form(None),
    student_class: str | None = Form(None),
    section: str | None = Form(None),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = await request.json()
        roll_no = roll_no or payload.get("roll_no")
        student_class = student_class or payload.get("student_class")
        section = section or payload.get("section")
        password = password or payload.get("password")

    roll_no = (roll_no or "").strip()
    student_class = (student_class or "1").strip()
    section = (section or "A").strip().upper()
    password = (password or "").strip()

    if not roll_no or not password:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={"school_name": SCHOOL_NAME, "error_message": "Please enter roll no and password."},
                status_code=422,
            )
        raise HTTPException(status_code=422, detail="roll_no and password are required")

    student_class_norm = student_class if student_class in {str(i) for i in range(1, 6)} else "1"
    section_norm = section if section in {"A", "B"} else "A"
    student = auth.authenticate_student(db, roll_no, student_class_norm, section_norm, password)
    if not student:
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={
                    "school_name": SCHOOL_NAME,
                    "error_message": "Oops! Invalid credentials for this class/section. Please check and try again.",
                },
                status_code=400,
            )
        raise HTTPException(status_code=400, detail="Invalid credentials")

    sc = getattr(student, "student_class", None) or student_class_norm
    sec = getattr(student, "section", None) or section_norm
    marks = build_marks_for_student(student.cgpa or 0.0)
    student_data = {
        "id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "student_class": sc,
        "section": sec,
        "class_label": f"Class {sc} Sec {sec}",
        "attendance": student.attendance,
        "cgpa": student.cgpa,
        "marks": marks,
        "subjects": SUBJECTS,
        "timetable": build_timetable(sc, sec),
        "notes": reference_notes(sc, sec),
        "initials": profile_initials(student.name),
        "fees": build_fees_details(student.roll_no, sc),
        "school_name": SCHOOL_NAME,
    }

    # Browser form submit -> show dashboard
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request=request,
            name="student_dashboard.html",
            context={"student": student_data, "school_name": SCHOOL_NAME},
        )

    # API/Swagger -> JSON response
    return {"message": f"Welcome {student.name}", "student": student_data}