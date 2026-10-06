"""
Unit-Tests für die Business Logic in services.py.
Prüft ECTS-Summen, gewichteten GPA, Zero-Division-Schutz, Wahlpflicht-Katalog und DRY JSON-Persistence.
"""

import os
import json
from datetime import datetime
from models import Module, StudyPlan
from services import (
    calculate_ects_summary,
    calculate_timeline,
    save_user_data,
    load_user_data,
    load_curriculum,
    load_electives_catalog,
    calculate_electives_summary,
)

CURRICULUM_PATH = "data/modules_medientechnik.json"


def test_calculate_ects_summary_and_weighted_gpa():
    plan = StudyPlan(student_name="Test Student", start_semester="WiSe", start_year=2024)
    
    # Benotetes Modul 1: 5 ECTS, Note 1.0
    m1 = Module(code="MT101", name="Mathe 1", ects=5, semester=1, is_lab=False, is_graded=True, passed=True, grade=1.0)
    # Benotetes Modul 2: 5 ECTS, Note 3.0
    m2 = Module(code="MT102", name="Physik 1", ects=5, semester=1, is_lab=False, is_graded=True, passed=True, grade=3.0)
    # Unbenotetes Labor: 3 ECTS, grade None, passed
    m3 = Module(code="MT104", name="Labor TI", ects=3, semester=1, is_lab=True, is_graded=False, passed=True, grade=None)
    # Offenes Modul: 5 ECTS
    m4 = Module(code="MT103", name="TI", ects=5, semester=1, is_lab=False, is_graded=True, passed=False)

    plan.add_module(m1)
    plan.add_module(m2)
    plan.add_module(m3)
    plan.add_module(m4)

    summary = calculate_ects_summary(plan)

    assert summary["ects_total"] == 18
    assert summary["ects_completed"] == 13
    assert summary["ects_remaining"] == 5
    assert summary["percentage"] == round((13 / 18) * 100.0, 1)

    # GPA Calculation: (1.0*5 + 3.0*5) / (5 + 5) = 20.0 / 10 = 2.0
    assert summary["weighted_gpa"] == 2.0


def test_calculate_electives_summary():
    plan = StudyPlan(student_name="Alice", start_semester="WiSe", start_year=2024)
    w1 = Module(code="M20", name="Audiotechnik und -produktion (T)", ects=5, semester=4, is_elective=True, passed=True)
    w2 = Module(code="M26", name="Lichtdesign (G)", ects=5, semester=5, is_elective=True, passed=True)
    w3 = Module(code="M28", name="Wahlmodul 3 (Technik)", ects=5, semester=6, is_elective=True, passed=False)

    plan.add_module(w1)
    plan.add_module(w2)
    plan.add_module(w3)

    summary = calculate_electives_summary(plan)
    assert summary["total_electives"] == 3
    assert summary["completed_electives"] == 2
    assert summary["technik_count"] == 2
    assert summary["gestaltung_count"] == 1


def test_calculate_timeline_zero_division_fallback():
    plan = StudyPlan(student_name="Freshman", start_semester="WiSe", start_year=2024)
    m1 = Module(code="MT101", name="Mathe 1", ects=5, semester=1, passed=False)
    plan.add_module(m1)

    current_date = datetime(2024, 10, 15)
    timeline = calculate_timeline(plan, current_date=current_date)

    assert timeline["current_fachsemester"] == 1
    assert timeline["is_pace_fallback"] is True
    assert timeline["pace_ects_per_sem"] == 30.0
    assert "2028" in timeline["regel_end_date"]


def test_calculate_timeline_normal_pace():
    plan = StudyPlan(student_name="Senior", start_semester="WiSe", start_year=2024)
    for i in range(12):
        plan.add_module(Module(code=f"MT{i}", name=f"Mod {i}", ects=5, semester=1, passed=True))
    for i in range(30):
        plan.add_module(Module(code=f"MT_OPEN_{i}", name=f"Open Mod {i}", ects=5, semester=2, passed=False))

    current_date = datetime(2025, 10, 15)
    timeline = calculate_timeline(plan, current_date=current_date)

    assert timeline["current_fachsemester"] == 3
    assert timeline["elapsed_semesters"] == 2
    assert timeline["is_pace_fallback"] is False
    assert timeline["pace_ects_per_sem"] == 30.0


def test_dry_save_and_load_user_data_lifecycle(tmp_path):
    test_file = os.path.join(tmp_path, "user_progress_dry.json")
    
    # Load base curriculum
    base_modules = load_curriculum(CURRICULUM_PATH)
    assert len(base_modules) > 0

    plan = StudyPlan(student_name="Alice", start_semester="SoSe", start_year=2024, modules=base_modules)
    
    # Mark first module completed
    target_mod = plan.modules[0]
    target_mod.mark_completed(1.7)

    # Save DRY
    success = save_user_data(plan, test_file)
    assert success
    assert os.path.exists(test_file)

    # Inspect JSON file to verify DRY rule (static attributes must NOT be duplicated)
    with open(test_file, "r", encoding="utf-8") as f:
        json_content = json.load(f)
    
    assert "module_states" in json_content
    assert target_mod.code in json_content["module_states"]
    # Static attributes like "ects" or "semester" must NOT be stored in user_progress.json
    assert "ects" not in json_content["module_states"][target_mod.code]

    # Load DRY
    loaded_plan = load_user_data(test_file, curriculum_path=CURRICULUM_PATH)
    assert loaded_plan is not None
    assert loaded_plan.student_name == "Alice"
    assert loaded_plan.start_semester == "SoSe"
    assert len(loaded_plan.modules) == len(base_modules)
    assert loaded_plan.modules[0].passed is True
    assert loaded_plan.modules[0].grade == 1.7


def test_load_curriculum_invalid_filepath():
    modules = load_curriculum("non_existent_file_xyz.json")
    assert modules == []


def test_load_electives_catalog():
    catalog = load_electives_catalog()
    assert "technik" in catalog
    assert "gestaltung" in catalog
    assert len(catalog["technik"]) > 0
    assert len(catalog["gestaltung"]) > 0


def test_timeline_zero_ects_completion_date():
    plan = StudyPlan(student_name="Neuling", start_semester="SoSe", start_year=2025)
    plan.add_module(Module(code="M1", name="Mathe", ects=5, semester=1, passed=False))
    
    tl = calculate_timeline(plan, current_date=datetime(2026, 9, 8))
    # Bei 0 ECTS muss das Abschlussdatum dem Regelstudienzeit-Abschluss entsprechen (28.07.2028),
    # und NICHT 2030 (heute + 3.5 Jahre) sein!
    assert tl["predicted_end_date"] == "28.07.2028"
    assert tl["regel_end_date"] == "28.07.2028"
    assert "Regelstudienzeit" in tl["calculation_basis"]


def test_calculate_age_at_date():
    from services import calculate_age_at_date
    
    # Valides Datum
    age = calculate_age_at_date("15.05.2002", "28.07.2028")
    assert age == 26
    
    # Leeres oder fehlendes Geburtsdatum -> None
    assert calculate_age_at_date("", "28.07.2028") is None
    assert calculate_age_at_date("invalid_date", "28.07.2028") is None


def test_format_grade():
    from services import format_grade
    assert format_grade(None, is_passed=False) == "Offen"
    assert format_grade(1.3, is_passed=True, is_graded=True) == "Note: 1.3"
    assert format_grade(None, is_passed=True, is_lab=True) == "Bestanden (Labor)"
    assert format_grade(None, is_passed=True, is_lab=False, is_graded=False) == "Bestanden (Unbenotet)"


def test_validate_birth_date():
    from services import validate_birth_date
    ok, val = validate_birth_date("15.03.2002")
    assert ok is True
    assert val == "15.03.2002"

    ok, err = validate_birth_date("31.02.2002")
    assert ok is False
    assert "existiert im Kalender nicht" in err

    ok, err = validate_birth_date("99.99.9999")
    assert ok is False

    ok, err = validate_birth_date("")
    assert ok is False


