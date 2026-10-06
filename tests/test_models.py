"""
Unit-Tests für die OOP-Klassen Module, TodoItem und StudyPlan in models.py.
"""

from models import Module, TodoItem, StudyPlan


def test_module_methods():
    mod = Module(code="MT101", name="Mathematik 1", ects=5, semester=1, is_lab=False)
    assert mod.code == "MT101"
    assert mod.name == "Mathematik 1"
    assert mod.ects == 5
    assert not mod.passed
    assert mod.grade is None

    # Test mark_completed
    mod.mark_completed(2.3)
    assert mod.passed
    assert mod.grade == 2.3

    # Test reset_status
    mod.reset_status()
    assert not mod.passed
    assert mod.grade is None

    # Test rename
    mod.rename("Höhere Mathematik 1")
    assert mod.name == "Höhere Mathematik 1"


def test_module_serialization():
    mod = Module(code="MT104", name="Labor TI", ects=3, semester=1, is_lab=True, is_elective=False, passed=True)
    data = mod.to_dict()
    assert data["code"] == "MT104"
    assert data["is_lab"] is True

    mod_restored = Module.from_dict(data)
    assert mod_restored.code == "MT104"
    assert mod_restored.is_lab is True
    assert mod_restored.passed is True


def test_todo_item_methods():
    todo = TodoItem(task_id=1, title="Laborbericht abgeben", due_date="15.10.2025", module_code="MT104")
    assert todo.task_id == 1
    assert not todo.is_done

    todo.toggle_status()
    assert todo.is_done
    todo.toggle_status()
    assert not todo.is_done

    data = todo.to_dict()
    todo_restored = TodoItem.from_dict(data)
    assert todo_restored.title == "Laborbericht abgeben"
    assert todo_restored.module_code == "MT104"


def test_study_plan_methods():
    plan = StudyPlan(student_name="Max Mustermann", start_semester="WiSe", start_year=2024)
    m1 = Module(code="MT101", name="Mathe 1", ects=5, semester=1)
    t1 = TodoItem(task_id=10, title="Übung lösen")

    plan.add_module(m1)
    plan.add_todo(t1)

    assert len(plan.modules) == 1
    assert len(plan.todos) == 1
    assert plan.get_module("MT101") == m1
    assert plan.get_module("NONEXISTENT") is None

    # Test remove todo
    removed = plan.remove_todo(10)
    assert removed
    assert len(plan.todos) == 0

    # Serialization test
    data = plan.to_dict()
    plan_restored = StudyPlan.from_dict(data)
    assert plan_restored.student_name == "Max Mustermann"
    assert len(plan_restored.modules) == 1
    assert plan_restored.modules[0].code == "MT101"


def test_study_plan_is_setup_done():
    # Neuer User ohne Name und ohne Flag -> nicht eingerichtet
    fresh_plan = StudyPlan()
    assert fresh_plan.is_setup_done() is False

    # Mit gesetztem Namen -> eingerichtet
    named_plan = StudyPlan(student_name="Dennis")
    assert named_plan.is_setup_done() is True

    # Mit explizitem Flag
    flag_plan = StudyPlan(setup_completed=True)
    assert flag_plan.is_setup_done() is True
