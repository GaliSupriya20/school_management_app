"""Shared helpers for student dashboard (timetable, marks demo, notes)."""

SUBJECTS = ["Maths", "Science", "English", "Social", "Computer"]

# Display name for headers / home page
SCHOOL_NAME = "Little Rainbow Academy"


def build_marks_for_student(cgpa: float) -> dict:
    base = int((cgpa or 0) * 10)
    marks_by_subject = {}
    for idx, subject in enumerate(SUBJECTS):
        fa1 = min(25, max(0, 12 + base // 4 + idx))
        fa2 = min(25, max(0, 11 + base // 4 + (idx % 3)))
        sa1 = min(25, max(0, 10 + base // 5 + (idx % 4)))
        sa2 = min(25, max(0, 9 + base // 5 + (idx % 5)))
        total = fa1 + fa2 + sa1 + sa2
        marks_by_subject[subject] = {
            "fa1": fa1,
            "fa2": fa2,
            "sa1": sa1,
            "sa2": sa2,
            "total": total,
        }
    return marks_by_subject


def build_timetable(student_class: str, section: str) -> list:
    """Simple weekly timetable rows for display."""
    return [
        {"day": "Monday", "p1": "Maths", "p2": "English", "p3": "Science", "p4": "Social"},
        {"day": "Tuesday", "p1": "Science", "p2": "Maths", "p3": "Computer", "p4": "English"},
        {"day": "Wednesday", "p1": "English", "p2": "Social", "p3": "Maths", "p4": "Science"},
        {"day": "Thursday", "p1": "Social", "p2": "Computer", "p3": "English", "p4": "Maths"},
        {"day": "Friday", "p1": "Computer", "p2": "Science", "p3": "Social", "p4": "English"},
        {"day": "Saturday", "p1": "Lab / Sports", "p2": "Revision", "p3": "-", "p4": "-"},
    ]


def reference_notes(student_class: str, section: str) -> str:
    return (
        f"Class {student_class or '1'} Section {section or 'A'} — "
        "Keep syllabus PDFs and chapter summaries here. "
        "Ask your faculty for official reference links and library codes."
    )


def profile_initials(name: str) -> str:
    parts = (name or "?").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (name[:2] or "?").upper()


def build_fees_details(roll_no: str, student_class: str) -> dict:
    """Demo fee summary (replace with real fee module later)."""
    try:
        sc = int(str(student_class or "1").strip())
    except ValueError:
        sc = 1
    sc = max(1, min(5, sc))
    term = 8000 + sc * 400
    paid = max(0, term - 1500)
    balance = term - paid
    return {
        "annual_fee": 42000,
        "term_fee": term,
        "paid": paid,
        "balance": balance,
        "due_date": "2026-04-15",
        "status": "Partially paid" if balance > 0 else "Paid",
        "roll_no": roll_no,
    }
