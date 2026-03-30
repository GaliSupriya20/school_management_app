from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    # roll_no is NOT globally unique; students are identified by (roll_no, student_class, section)
    roll_no = Column(String, index=True)
    name = Column(String)
    password = Column(String)
    cgpa = Column(Float)
    attendance = Column(Float)
    # Class 1–5 and section A/B (used to categorize students)
    student_class = Column(String, default="1")
    section = Column(String, default="A")

class Faculty(Base):
    __tablename__ = "faculties"
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)