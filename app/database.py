from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./college.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def migrate_sqlite_columns():
    """Add new columns to existing SQLite DB if missing."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE students ADD COLUMN student_class VARCHAR DEFAULT '1'"))
    except Exception:
        pass
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE students ADD COLUMN section VARCHAR DEFAULT 'A'"))
    except Exception:
        pass


def rebuild_students_table_allow_duplicate_rollno():
    """
    Rebuild SQLite `students` table to remove UNIQUE constraint on `roll_no`.
    This enables multiple students with the same roll_no across different classes/sections.
    """
    with engine.begin() as conn:
        # Clean up from any previous failed migration
        try:
            conn.execute(text("DROP TABLE IF EXISTS students_old"))
        except Exception:
            pass
        # Detect if there is a unique index that involves roll_no
        # If it doesn't exist, rebuilding is still safe (data is copied).
        conn.execute(text("ALTER TABLE students RENAME TO students_old"))

        conn.execute(
            text(
                """
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no VARCHAR,
                    name VARCHAR,
                    password VARCHAR,
                    cgpa FLOAT,
                    attendance FLOAT,
                    student_class VARCHAR DEFAULT '1',
                    section VARCHAR DEFAULT 'A'
                )
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO students (id, roll_no, name, password, cgpa, attendance, student_class, section)
                SELECT
                    id, roll_no, name, password, cgpa, attendance,
                    COALESCE(student_class, '1'),
                    COALESCE(section, 'A')
                FROM students_old
                """
            )
        )

        conn.execute(text("DROP TABLE students_old"))