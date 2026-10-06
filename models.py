# models.py - Datenmodelle für den Studienplaner
# Geschrieben von Johann (HAW Medientechnik, Semester 3)

class Module:
    """Repräsentiert ein einzelnes Fach oder Modul im Studienplan."""

    def __init__(self, code, name, ects, semester, is_lab=False, is_graded=True, is_elective=False, passed=False, grade=None):
        """Initialisiert ein Modul mit seinen Eigenschaften."""
        # Eigenschaften eines Faches speichern
        self.code = code
        self.name = name
        self.ects = ects
        self.semester = semester
        self.is_lab = is_lab
        self.is_graded = is_graded
        self.is_elective = is_elective
        self.passed = passed
        self.grade = grade

    def mark_completed(self, grade=None):
        """Fach als bestanden abhaken und Note speichern (falls benotet)."""
        # Fach als bestanden markieren (Note nur eintragen, wenn das Fach benotet wurde)
        self.passed = True
        self.grade = grade if self.is_graded else None

    def reset_status(self):
        """Status wieder auf offen zurücksetzen."""
        # Zurücksetzen auf Status "offen", falls man sich verklickt hat
        self.passed = False
        self.grade = None

    def rename(self, new_name):
        """Namen des Moduls anpassen (z.B. bei Wahlpflichtfächern)."""
        # Namen anpassen (benötigt, wenn man ein Wahlpflichtfach aussucht)
        if new_name and new_name.strip():
            self.name = new_name.strip()

    def to_dict(self):
        """Konvertiert das Modul in ein Dictionary für JSON."""
        return {
            "code": self.code,
            "name": self.name,
            "ects": self.ects,
            "semester": self.semester,
            "is_lab": self.is_lab,
            "is_graded": self.is_graded,
            "is_elective": self.is_elective,
            "passed": self.passed,
            "grade": self.grade
        }

    @classmethod
    def from_dict(cls, data):
        """Erstellt ein Modul-Objekt aus einem Dictionary."""
        return cls(
            code=data.get("code", ""),
            name=data.get("name", ""),
            ects=data.get("ects", 0),
            semester=data.get("semester", 1),
            is_lab=data.get("is_lab", False),
            is_graded=data.get("is_graded", True),
            is_elective=data.get("is_elective", False),
            passed=data.get("passed", False),
            grade=data.get("grade")
        )


class TodoItem:
    """Eine Aufgabe für die To-Do-Liste in der App."""

    def __init__(self, task_id, title, due_date="", module_code="", is_done=False):
        """Initialisiert eine To-Do-Aufgabe."""
        # Variablen für eine Aufgabe
        self.task_id = task_id
        self.title = title
        self.due_date = due_date
        self.module_code = module_code
        self.is_done = is_done

    def toggle_status(self):
        """Wechselt den Status zwischen erledigt und offen."""
        # Einfach zwischen abgehakt und offen hin und her wechseln
        self.is_done = not self.is_done

    def to_dict(self):
        """Konvertiert die Aufgabe in ein Dictionary für JSON."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "due_date": self.due_date,
            "module_code": self.module_code,
            "is_done": self.is_done
        }

    @classmethod
    def from_dict(cls, data):
        """Erstellt ein TodoItem-Objekt aus einem Dictionary."""
        return cls(
            task_id=data.get("task_id", 0),
            title=data.get("title", ""),
            due_date=data.get("due_date", ""),
            module_code=data.get("module_code", ""),
            is_done=data.get("is_done", False)
        )


class StudyPlan:
    """Verwaltet den gesamten Studienplan inklusive Modulen und To-Dos."""

    def __init__(self, student_name="", start_semester="SoSe", start_year=2025, modules=None, todos=None, birth_date="", setup_completed=False):
        """Initialisiert den Studienplan eines Studierenden."""
        # Hier halten wir den ganzen Studienplan zusammen (alle Fächer + Aufgaben)
        self.student_name = student_name
        self.start_semester = start_semester
        self.start_year = start_year
        self.birth_date = birth_date
        self.setup_completed = setup_completed
        self.modules = modules if modules is not None else []
        self.todos = todos if todos is not None else []

    def is_setup_done(self):
        """Prüft, ob die Ersteinrichtung bereits abgeschlossen wurde."""
        # Überprüfung, ob der User schon eingerichtet ist (dann direkt aufs Dashboard)
        return bool(self.setup_completed or (self.student_name and self.student_name.strip()))

    def add_module(self, module):
        """Fügt ein neues Modul zum Studienplan hinzu."""
        # Neues Fach anhängen
        self.modules.append(module)

    def add_todo(self, todo):
        """Fügt neue To-Do-Aufgabe hinzu."""
        # Neue Aufgabe anhängen
        self.todos.append(todo)

    def remove_todo(self, task_id):
        """Entfernt eine Aufgabe anhand ihrer ID."""
        # Aufgabe anhand der ID wieder rauswerfen
        before = len(self.todos)
        self.todos = [t for t in self.todos if t.task_id != task_id]
        return len(self.todos) < before

    def get_module(self, code):
        """Sucht ein Modul anhand seines Kürzels (z.B. 'M1')."""
        # Modul über das Kürzel finden (z.B. 'M1')
        for m in self.modules:
            if m.code.lower() == code.lower():
                return m
        return None

    def to_dict(self):
        """Konvertiert den Studienplan in ein Dictionary für JSON."""
        return {
            "student_name": self.student_name,
            "start_semester": self.start_semester,
            "start_year": self.start_year,
            "birth_date": self.birth_date,
            "setup_completed": self.setup_completed,
            "modules": [m.to_dict() for m in self.modules],
            "todos": [t.to_dict() for t in self.todos]
        }

    @classmethod
    def from_dict(cls, data):
        """Erstellt ein StudyPlan-Objekt aus einem Dictionary."""
        modules = [Module.from_dict(m) for m in data.get("modules", [])]
        todos = [TodoItem.from_dict(t) for t in data.get("todos", [])]
        name = data.get("student_name", "")
        return cls(
            student_name=name,
            start_semester=data.get("start_semester", "SoSe"),
            start_year=data.get("start_year", 2025),
            modules=modules,
            todos=todos,
            birth_date=data.get("birth_date", ""),
            setup_completed=data.get("setup_completed", bool(name and name.strip()))
        )
