# services.py - Berechnungen, Logik und Dateiverwaltung
# Geschrieben von Dennis (HAW Medientechnik)

import json
import os
from datetime import datetime, timedelta

from models import Module, StudyPlan, TodoItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CURRICULUM_PATH = os.path.join(BASE_DIR, "data", "modules_medientechnik.json")
USER_PROGRESS_PATH = os.path.join(BASE_DIR, "data", "user_progress.json")
ELECTIVES_CATALOG_PATH = os.path.join(BASE_DIR, "data", "electives_catalog.json")


def load_curriculum(filepath=CURRICULUM_PATH):
    """Lädt die Liste aller Standard-Module aus der Curriculum-JSON-Datei."""
    # Lädt die Fächerliste aus der modules_medientechnik.json
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Module.from_dict(item) for item in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_electives_catalog(filepath=ELECTIVES_CATALOG_PATH):
    """Lädt den Wahlpflichtkatalog für Technik und Gestaltung aus der JSON-Datei."""
    # Lädt den Wahlpflichtkatalog für Technik und Gestaltung
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"rules": {}, "technik": [], "gestaltung": []}


def format_grade(grade, is_passed=False, is_lab=False, is_graded=True):
    """Formatiert eine Note oder den Prüfungsstatus für die Anzeige."""
    # Note für die Anzeige formatieren (z.B. 'Note: 1.3' oder 'Offen')
    if not is_passed:
        return "Offen"
    if is_graded and grade is not None and grade > 0.0:
        return f"Note: {grade:.1f}"
    if is_lab:
        return "Bestanden (Labor)"
    return "Bestanden (Unbenotet)"


def save_user_data(plan, filepath=USER_PROGRESS_PATH):
    """Speichert den aktuellen Studienplan und Aufgaben in eine JSON-Datei."""
    # Speichert den aktuellen Studienstand in die user_progress.json Datei
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        module_states = {}
        for m in plan.modules:
            state = {"passed": m.passed, "grade": m.grade}
            if m.is_elective and m.name:
                state["custom_name"] = m.name
            module_states[m.code] = state

        data = {
            "student_name": plan.student_name,
            "start_semester": plan.start_semester,
            "start_year": plan.start_year,
            "birth_date": getattr(plan, "birth_date", ""),
            "setup_completed": getattr(plan, "setup_completed", False),
            "module_states": module_states,
            "todos": [t.to_dict() for t in plan.todos]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError):
        return False


def load_user_data(filepath=USER_PROGRESS_PATH, curriculum_path=CURRICULUM_PATH):
    """Lädt gespeicherte Nutzerdaten und wendet sie auf das Standard-Curriculum an."""
    # Lädt die Fächer und trägt die gespeicherten Noten oder Haken wieder ein
    if not os.path.exists(filepath):
        return None

    try:
        modules = load_curriculum(curriculum_path)
        if not modules:
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            user_data = json.load(f)

        module_states = user_data.get("module_states", {})
        for m in modules:
            if m.code in module_states:
                st = module_states[m.code]
                m.passed = st.get("passed", False)
                m.grade = st.get("grade")
                if "custom_name" in st and st["custom_name"]:
                    m.name = st["custom_name"]

        todos = [TodoItem.from_dict(t) for t in user_data.get("todos", [])]

        return StudyPlan(
            student_name=user_data.get("student_name", ""),
            start_semester=user_data.get("start_semester", "SoSe"),
            start_year=user_data.get("start_year", 2025),
            modules=modules,
            todos=todos,
            birth_date=user_data.get("birth_date", ""),
            setup_completed=user_data.get("setup_completed", bool(user_data.get("student_name", "").strip()))
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def calculate_ects_summary(plan):
    """Berechnet die ECTS-Summen, offenen ECTS und den gewichteten Notenschnitt."""
    # ECTS zusammenrechnen und den gewichteten Notenschnitt berechnen
    total_ects = sum(m.ects for m in plan.modules) if plan.modules else 210
    completed_ects = 0
    
    # Notenschnitt gewichtet nach ECTS ausrechnen
    weighted_sum = 0.0
    graded_ects = 0
    passed_modules = 0
    total_modules = 0
    passed_labs = 0
    open_labs = 0
    total_labs = 0

    for m in plan.modules:
        if m.passed:
            completed_ects = completed_ects + m.ects
        
        if m.is_lab:
            total_labs = total_labs + 1
            if m.passed:
                passed_labs = passed_labs + 1
            else:
                open_labs = open_labs + 1
        else:
            total_modules = total_modules + 1
            if m.passed:
                passed_modules = passed_modules + 1

        if m.passed and m.is_graded and m.grade is not None and m.grade > 0.0:
            weighted_sum = weighted_sum + (m.grade * m.ects)
            graded_ects = graded_ects + m.ects

    remaining_ects = max(0, total_ects - completed_ects)
    percentage = (completed_ects / total_ects * 100.0) if total_ects > 0 else 0.0
    weighted_gpa = round(weighted_sum / graded_ects, 2) if graded_ects > 0 else None

    return {
        "ects_total": total_ects,
        "ects_completed": completed_ects,
        "ects_remaining": remaining_ects,
        "percentage": round(percentage, 1),
        "weighted_gpa": weighted_gpa,
        "passed_modules_count": passed_modules,
        "total_modules_count": total_modules,
        "open_labs_count": open_labs,
        "passed_labs_count": passed_labs,
        "total_labs_count": total_labs,
    }


def calculate_electives_summary(plan):
    """Ermittelt die Anzahl und Verteilung abgeschlossener Wahlpflichtfächer."""
    # Wahlpflichtfächer prüfen (4 Technik, 2 Gestaltung, 1 Frei)
    electives = []
    completed_count = 0
    for m in plan.modules:
        if m.is_elective:
            electives.append(m)
            if m.passed:
                completed_count = completed_count + 1

    gestaltung_keywords = ["(g)", "gestaltung", "dramaturgie", "lichtdesign", "musikproduktion", "filmton", "media design"]
    gestaltung_count = 0
    technik_count = 0

    for m in electives:
        n = m.name.lower()
        ist_gestaltung = False
        for k in gestaltung_keywords:
            if k in n:
                ist_gestaltung = True
                break
        if ist_gestaltung:
            gestaltung_count = gestaltung_count + 1
        else:
            technik_count = technik_count + 1

    return {
        "total_electives": len(electives),
        "completed_electives": completed_count,
        "technik_count": technik_count,
        "gestaltung_count": gestaltung_count,
        "required_technik": 4,
        "required_gestaltung": 2,
        "required_free": 1
    }


def _get_semester_start_date(start_semester, start_year):
    """Ermittelt das kalendarische Startdatum eines Semesters (WiSe/SoSe)."""
    # Semesterbeginn: WiSe = 1. Oktober, SoSe = 1. April
    if start_semester.lower().startswith("wise") or "winter" in start_semester.lower():
        return datetime(start_year, 10, 1)
    return datetime(start_year, 4, 1)


def calculate_timeline(plan, current_date=None):
    """Berechnet aktuelles Fachsemester, Regelstudienzeit und prognostiziertes Enddatum."""
    # Berechnet aktuelles Fachsemester und voraussichtlichen Abschluss
    if current_date is None:
        current_date = datetime.now()

    start_date = _get_semester_start_date(plan.start_semester, plan.start_year)
    days_elapsed = (current_date - start_date).days
    
    if days_elapsed < 0:
        elapsed_semesters = 0
        current_fachsemester = 1
    else:
        elapsed_semesters = int(days_elapsed // 182.5)
        current_fachsemester = elapsed_semesters + 1

    # Enddatum der Regelstudienzeit (7 Semester)
    if plan.start_semester.lower().startswith("wise") or "winter" in plan.start_semester.lower():
        regel_end_date = datetime(plan.start_year + 4, 3, 31)
        regel_end_term_str = f"WiSe {plan.start_year+3}/{str(plan.start_year+4)[-2:]}"
    else:
        # SoSe: 7 Semester enden Ende Juli (28.07.)
        regel_end_date = datetime(plan.start_year + 3, 7, 28)
        regel_end_term_str = f"SoSe {plan.start_year+3}"

    remaining_days_regel = (regel_end_date - current_date).days
    summary = calculate_ects_summary(plan)
    completed_ects = summary["ects_completed"]
    remaining_ects = summary["ects_remaining"]

    if elapsed_semesters <= 0 or completed_ects <= 0:
        pace_ects_per_sem = 30.0
        is_fallback = True
        remaining_semesters_needed = float(max(1, 7 - elapsed_semesters))
        predicted_end_date = regel_end_date
        calculation_basis = f"Regelstudienzeit (7 Semester bis {regel_end_term_str}, 30 ECTS/Semester)"
    else:
        pace_ects_per_sem = completed_ects / elapsed_semesters
        is_fallback = False
        remaining_semesters_needed = remaining_ects / pace_ects_per_sem if pace_ects_per_sem > 0 else 0.0
        predicted_end_date = current_date + timedelta(days=int(remaining_semesters_needed * 182.5))
        calculation_basis = f"Bisheriges Tempo ({pace_ects_per_sem:.1f} ECTS/Semester) bei noch {remaining_ects} offenen ECTS"

    return {
        "current_fachsemester": current_fachsemester,
        "elapsed_semesters": elapsed_semesters,
        "regel_end_date": regel_end_date.strftime("%d.%m.%Y"),
        "regel_end_term": regel_end_term_str,
        "remaining_days_regel": max(0, remaining_days_regel),
        "pace_ects_per_sem": round(pace_ects_per_sem, 1),
        "is_pace_fallback": is_fallback,
        "predicted_end_date": predicted_end_date.strftime("%d.%m.%Y"),
        "remaining_semesters_needed": round(remaining_semesters_needed, 1),
        "calculation_basis": calculation_basis,
    }


def calculate_age_at_date(birth_date_str, target_date_str):
    """Berechnet das Alter in vollen Jahren zu einem bestimmten Stichtag."""
    # Rechnet aus wie alt man am Abschluss-Tag ist (in vollen Jahren)
    if not birth_date_str or not target_date_str:
        return None

    def _parse(s):
        """Hilfsfunktion zum Parsen von Datumsstrings."""
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s.strip(), fmt)
            except ValueError:
                pass
        return None

    b_date = _parse(birth_date_str)
    t_date = _parse(target_date_str)
    if not b_date or not t_date:
        return None

    age = t_date.year - b_date.year - ((t_date.month, t_date.day) < (b_date.month, b_date.day))
    return max(0, age)


def validate_birth_date(date_str):
    """Validiert ein Geburtsdatum auf Format, Gültigkeit und Mindestalter."""
    # Geburtsdatum check: Format TT.MM.JJJJ, ob der Kalendertag existiert und Alter zwischen 16 und 99
    if not date_str:
        return False, "Bitte gib dein Geburtsdatum ein."

    clean = date_str.strip().replace(" ", "").replace("_", "")
    parts = clean.split(".")
    if len(parts) != 3:
        return False, "Format muss TT.MM.JJJJ sein (z.B. 15.03.2002)."

    tag_str, monat_str, jahr_str = parts
    if not (tag_str.isdigit() and monat_str.isdigit() and jahr_str.isdigit()):
        return False, "Das Datum darf nur Ziffern enthalten."

    if len(jahr_str) != 4 or len(tag_str) == 0 or len(monat_str) == 0:
        return False, "Format muss TT.MM.JJJJ sein (z.B. 15.03.2002)."

    tag, monat, jahr = int(tag_str), int(monat_str), int(jahr_str)

    try:
        b_date = datetime(jahr, monat, tag)
    except ValueError:
        return False, "Dieses Datum existiert im Kalender nicht."

    today = datetime.now()
    if b_date > today:
        return False, "Das Datum darf nicht in der Zukunft liegen."

    alter = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    if alter < 16:
        return False, "Mindestalter fuer das Studium ist 16 Jahre."
    if alter > 99:
        return False, "Bitte gib ein gueltiges Geburtsjahr an."

    formatted = f"{tag:02d}.{monat:02d}.{jahr:04d}"
    return True, formatted


def validate_due_date(date_str):
    """Prüft, ob ein eingegebenes Frist-Datum für eine Aufgabe gültig ist."""
    if not date_str or not date_str.strip():
        return True, ""

    clean = date_str.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            d = datetime.strptime(clean, fmt)
            if 2020 <= d.year <= 2035:
                return True, d.strftime("%d.%m.%Y")
        except ValueError:
            pass

    return False, "Bitte ein gültiges Datum im Format TT.MM.JJJJ eingeben (z. B. 30.10.2025)."
