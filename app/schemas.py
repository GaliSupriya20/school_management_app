from pydantic import BaseModel

class StudentBase(BaseModel):
    name: str
    roll_no: str

class StudentCreate(StudentBase):
    password: str

class Student(StudentBase):
    id: int
    cgpa: float

    class Config:
        orm_mode = True

class FacultyBase(BaseModel):
    name: str
    emp_id: str

class FacultyCreate(FacultyBase):
    password: str

class Faculty(FacultyBase):
    id: int

    class Config:
        orm_mode = True

