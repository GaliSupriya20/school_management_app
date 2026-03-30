from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine, migrate_sqlite_columns, rebuild_students_table_allow_duplicate_rollno
from app.routers import faculty, student
from app.student_dashboard_data import SCHOOL_NAME

Base.metadata.create_all(bind=engine)
migrate_sqlite_columns()
rebuild_students_table_allow_duplicate_rollno()

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(student.router)
app.include_router(faculty.router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"school_name": SCHOOL_NAME},
    )