from passlib.context import CryptContext
from sqlalchemy.orm import Session

import app.models as models

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_student(db: Session, roll_no: str, student_class: str, section: str, password: str):
    student = (
        db.query(models.Student)
        .filter(
            models.Student.roll_no == roll_no,
            models.Student.student_class == student_class,
            models.Student.section == section,
        )
        .first()
    )
    if student and verify_password(password, student.password):
        return student
    return None


def authenticate_faculty(db: Session, faculty_id: str, password: str):
    faculty = db.query(models.Faculty).filter(models.Faculty.faculty_id == faculty_id).first()
    if faculty and verify_password(password, faculty.password):
        return faculty
    return None