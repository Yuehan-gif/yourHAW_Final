# setup_views.py - Startbildschirme und Dialoge für die Ersteinrichtung
# Geschrieben von Janina (HAW Medientechnik)

from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QScrollArea,
    QDialog,
    QFormLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QGroupBox,
)

from models import StudyPlan, Module
from services import (
    save_user_data,
    validate_birth_date,
    validate_due_date,
    load_electives_catalog,
    USER_PROGRESS_PATH,
)

# Erlaubte Noten und die dazugehörigen Texte für das Auswahlfeld.
VALID_GRADES = [
    (0.7, "0.7 (Ausgezeichnet)"),
    (1.0, "1.0 (Sehr gut)"),
    (1.3, "1.3 (Sehr gut)"),
    (1.7, "1.7 (Gut)"),
    (2.0, "2.0 (Gut)"),
    (2.3, "2.3 (Gut)"),
    (2.7, "2.7 (Befriedigend)"),
    (3.0, "3.0 (Befriedigend)"),
    (3.3, "3.3 (Befriedigend)"),
    (3.7, "3.7 (Ausreichend)"),
    (4.0, "4.0 (Ausreichend)"),
    (5.0, "5.0 (Nicht bestanden)"),
]


class IntroScreen(QWidget):
    """Erster Begrüßungsbildschirm mit Wechseltext und Start-Button."""

    def __init__(self, on_start_callback, parent=None):
        """Initialisiert die Willkommensansicht."""
        super().__init__(parent)
        self.on_start_callback = on_start_callback

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title_lbl = QLabel("Your HAW")
        title_lbl.setStyleSheet("font-size: 44px; font-weight: bold;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        # Diese Texte werden auf der Startseite nacheinander angezeigt.
        self.subtitles = [
            "Einfach.",
            "Übersicht behalten.",
            "Fortschritt tracken.",
            "Dein Studium planen.",
        ]
        self.current_sub_idx = 0

        self.sub_lbl = QLabel(self.subtitles[0])
        self.sub_lbl.setStyleSheet("font-size: 16px; min-height: 28px;")
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_lbl)

        layout.addSpacing(16)

        self.start_btn = QPushButton("Start  ->")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setFixedWidth(180)
        self.start_btn.setFixedHeight(38)
        self.start_btn.clicked.connect(self.on_start_callback)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Der Timer wechselt den Untertitel alle 2,5 Sekunden.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._cycle_subtitle)
        self.timer.start(2500)

    def _cycle_subtitle(self):
        """Wechselt periodisch den angezeigten Untertitel."""
        # Durch den Restoperator beginnt die Liste nach dem letzten Text wieder von vorn.
        self.current_sub_idx = (self.current_sub_idx + 1) % len(self.subtitles)
        self.sub_lbl.setText(self.subtitles[self.current_sub_idx])


class SetupStep1Screen(QWidget):
    """Schritt 1 der Ersteinrichtung: Name, Geburtsdatum, Studiengang."""

    def __init__(self, plan, on_next, on_cancel, parent=None):
        """Initialisiert Schritt 1 des Setup-Assistenten."""
        super().__init__(parent)
        self.plan = plan
        self.on_next = on_next
        self.on_cancel = on_cancel

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        group_box = QGroupBox("Einrichtung 1/2: Deine Daten")
        group_box.setFixedWidth(440)

        form_layout = QVBoxLayout(group_box)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Dein Name:"))
        self.name_input = QLineEdit(plan.student_name or "")
        self.name_input.setPlaceholderText("z. B. Max Mustermann")
        form_layout.addWidget(self.name_input)

        form_layout.addWidget(QLabel("Geburtsdatum (TT.MM.JJJJ):"))
        self.birth_input = QLineEdit(getattr(plan, "birth_date", "") or "")
        self.birth_input.setPlaceholderText("TT.MM.JJJJ")
        # Die Eingabemaske gibt erwartetes Datumsformat vor.
        self.birth_input.setInputMask("99.99.9999;_")
        form_layout.addWidget(self.birth_input)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: red; font-weight: bold;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        form_layout.addWidget(self.error_lbl)

        form_layout.addWidget(QLabel("Studiengang:"))
        self.studiengang_combo = QComboBox()
        self.studiengang_combo.addItem("Medientechnik (B.Sc.)")
        form_layout.addWidget(self.studiengang_combo)

        form_layout.addWidget(QLabel("Startsemester:"))
        self.sem_combo = QComboBox()
        self.sem_combo.addItem("SoSe 25")
        self.sem_combo.addItem("WiSe 24/25")
        self.sem_combo.addItem("SoSe 24")
        form_layout.addWidget(self.sem_combo)

        form_layout.addSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("<- Abbrechen")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.on_cancel)
        btn_row.addWidget(cancel_btn)

        next_btn = QPushButton("Weiter ->")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._save_and_next)
        btn_row.addWidget(next_btn)

        form_layout.addLayout(btn_row)
        layout.addWidget(group_box)

    def reset_fields(self):
        """Setzt die Eingabefelder für einen frischen Neustart zurück."""
        self.name_input.setText("")
        self.birth_input.setText("")
        self.error_lbl.setText("")
        self.error_lbl.hide()

    def _save_and_next(self):
        """Validiert die Daten und wechselt zu Schritt 2."""
        # Leere Namen werden nicht übernommen.
        name = self.name_input.text().strip()
        if not name:
            self.error_lbl.setText("Bitte gib deinen Namen ein.")
            self.error_lbl.show()
            return

        birth_raw = self.birth_input.text().strip()
        # Eigentliche Datumsprüfung findet zentral im Service-Modul statt.
        ok, res = validate_birth_date(birth_raw)
        if not ok:
            self.error_lbl.setText(res)
            self.error_lbl.show()
            return

        self.error_lbl.hide()
        birth_date = res

        # Aus "SoSe 25" werden Semesterart und vierstellige Jahreszahl getrennt.
        sem_str = self.sem_combo.currentText()
        parts = sem_str.split(" ")
        start_sem = parts[0]
        yr_suffix = parts[1] if len(parts) > 1 else "25"
        start_year = 2000 + int(yr_suffix[:2]) if yr_suffix[:2].isdigit() else 2025

        self.plan.student_name = name
        self.plan.birth_date = birth_date
        self.plan.start_semester = start_sem
        self.plan.start_year = start_year
        # Persönlichen Angaben werden vor nächstem Schritt gespeichert.
        save_user_data(self.plan, USER_PROGRESS_PATH)

        self.on_next()


OnboardingDialog = SetupStep1Screen


class SetupStep2Screen(QWidget):
    """Schritt 2 der Ersteinrichtung: Vorleistungen und Noten erfassen."""

    def __init__(self, plan, on_back, on_finish, parent=None):
        """Initialisiert Schritt 2 des Setup-Assistenten."""
        super().__init__(parent)
        self.plan = plan
        self.on_back = on_back
        self.on_finish = on_finish

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        title_lbl = QLabel("Einrichtung 2/2: Vorleistungen")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        hint = QLabel("Klicke auf ein Modul, um es als bestanden zu markieren oder eine Note einzutragen.")
        top_bar.addWidget(hint)
        layout.addLayout(top_bar)

        # Durch Scrollbereich bleiben alle sieben Semester erreichbar.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.StyledPanel)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.step2_container = QWidget()
        self.cols_layout = QHBoxLayout(self.step2_container)
        self.cols_layout.setSpacing(12)
        self.cols_layout.setContentsMargins(8, 8, 8, 12)

        scroll.setWidget(self.step2_container)
        layout.addWidget(scroll, 1)

        bottom_row = QHBoxLayout()
        back_btn = QPushButton("<- Zurück")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.on_back)
        bottom_row.addWidget(back_btn)
        bottom_row.addStretch()

        finish_btn = QPushButton("Einrichtung abschließen ✓")
        finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        finish_btn.clicked.connect(self._save_and_finish)
        bottom_row.addWidget(finish_btn)

        layout.addLayout(bottom_row)
        self.refresh_columns()

    def refresh_columns(self):
        """Baut die 7 Semester-Spalten mit den Modulen neu auf."""
        # Vor Neuaufbau werden bisher angezeigte Semesterkarten entfernt.
        while self.cols_layout.count():
            item = self.cols_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        col_w = 260
        # Für jedes Semester wird eine eigene Spalte erzeugt.
        for sem in range(1, 8):
            col_box = QGroupBox(f"{sem}. Semester")
            col_box.setFixedWidth(col_w)
            c_lay = QVBoxLayout(col_box)
            c_lay.setSpacing(6)
            c_lay.setContentsMargins(6, 10, 6, 6)

            sem_mods = [m for m in self.plan.modules if m.semester == sem]
            for m in sem_mods:
                m_btn = QPushButton()
                m_btn.setCursor(Qt.CursorShape.PointingHandCursor)

                status_txt = "Bestanden" if m.passed else "Offen"
                grade_txt = f" - Note {m.grade}" if (m.passed and m.grade) else ""
                m_btn.setText(f"{m.code}: {m.name}\n[{status_txt}{grade_txt}]")

                if m.passed:
                    m_btn.setStyleSheet("background-color: #c8e6c9; text-align: left;")
                else:
                    m_btn.setStyleSheet("text-align: left;")

                # mod=m bindet den Button dauerhaft an das jeweilige Modul.
                m_btn.clicked.connect(lambda checked=False, mod=m: self._edit_mod(mod))
                c_lay.addWidget(m_btn)

            c_lay.addStretch()
            self.cols_layout.addWidget(col_box)

        self.cols_layout.addStretch()
        self.step2_container.setMinimumWidth(7 * col_w + (6 * 12) + 30)

    def _edit_mod(self, mod):
        """Öffnet den Dialog zum Bearbeiten eines Moduls."""
        dlg = EditModuleDialog(mod, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply_changes()
            save_user_data(self.plan, USER_PROGRESS_PATH)
            self.refresh_columns()

    def _save_and_finish(self):
        """Schließt die Einrichtung ab und speichert den Stand."""
        save_user_data(self.plan, USER_PROGRESS_PATH)
        self.on_finish()


class EditModuleDialog(QDialog):
    """Dialogfenster zur Anpassung von Status und Note eines Moduls."""

    def __init__(self, module, parent=None):
        """Initialisiert den Bearbeitungsdialog für ein Modul."""
        super().__init__(parent)
        self.module = module
        self.setWindowTitle(f"Modul bearbeiten: {module.code}")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        info_lbl = QLabel(f"<b>{module.code}</b> - {module.name}<br>ECTS: {module.ects} | {module.semester}. Semester")
        layout.addWidget(info_lbl)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Offen", "Bestanden"])
        self.status_combo.setCurrentIndex(1 if module.passed else 0)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form_layout.addRow("Status:", self.status_combo)

        # Bei unbenoteten Laboren wird kein Notenfeld angezeigt.
        if not module.is_graded:
            form_layout.addRow("Bewertung:", QLabel("Unbenotet (Labor)"))
            self.grade_combo = None
        else:
            self.grade_combo = QComboBox()
            for val, text in VALID_GRADES:
                self.grade_combo.addItem(text, val)

            # Ohne vorhandene Note wird 2,0 als Startwert ausgewählt.
            cur_grade = module.grade if (module.grade is not None and module.grade > 0.0) else 2.0
            idx = 0
            for i, (val, _) in enumerate(VALID_GRADES):
                if abs(val - cur_grade) < 0.05:
                    idx = i
                    break
            self.grade_combo.setCurrentIndex(idx)
            self.grade_combo.setEnabled(module.passed)
            form_layout.addRow("Offizielle Note:", self.grade_combo)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.accept)

        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _on_status_changed(self, text):
        """Aktiviert oder deaktiviert das Notenfeld je nach Status."""
        if self.grade_combo:
            self.grade_combo.setEnabled(text == "Bestanden")

    def apply_changes(self):
        """Überträgt die gewählten Änderungen auf das Modul."""
        is_passed = (self.status_combo.currentText() == "Bestanden")
        # Ein offenes Modul verliert eine eventuell zuvor gespeicherte Note.
        if not is_passed:
            self.module.reset_status()
        else:
            if not self.module.is_graded:
                self.module.mark_completed(grade=None)
            else:
                grade_val = self.grade_combo.currentData() if self.grade_combo else None
                self.module.mark_completed(grade=grade_val)


class SelectElectiveFromCatalogDialog(QDialog):
    """Dialog zur Auswahl eines Wahlpflichtfachs aus dem HAW-Katalog."""

    def __init__(self, current_module, parent=None):
        """Initialisiert den Katalogauswahldialog."""
        super().__init__(parent)
        self.module = current_module
        self.setWindowTitle(f"Wahlpflichtfach wählen ({current_module.code})")
        self.resize(520, 420)

        # Der Wahlpflichtkatalog wird aus der zugehörigen JSON-Datei geladen.
        self.catalog = load_electives_catalog()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info = QLabel("<b>Vorgabe Medientechnik:</b> Insgesamt 7 Wahlpflichtfächer (35 ECTS). Mindestens 4x Technik, 2x Gestaltung.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fachname", "Bereich", "Prüfungsform"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 100)

        # Technische und gestalterische Fächer erhalten getrennte Hauptkategorien.
        tech_root = QTreeWidgetItem(self.tree, ["Technik (T)", "Technik", ""])
        tech_root.setExpanded(True)
        for item in self.catalog.get("technik", []):
            child = QTreeWidgetItem(tech_root, [item["name"], "Technik (T)", item.get("exam", "")])
            child.setData(0, Qt.ItemDataRole.UserRole, f"{item['name']} (T)")

        gest_root = QTreeWidgetItem(self.tree, ["Gestaltung (G)", "Gestaltung", ""])
        gest_root.setExpanded(True)
        for item in self.catalog.get("gestaltung", []):
            child = QTreeWidgetItem(gest_root, [item["name"], "Gestaltung (G)", item.get("exam", "")])
            child.setData(0, Qt.ItemDataRole.UserRole, f"{item['name']} (G)")

        layout.addWidget(self.tree)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Oder eigenen Fachnamen manuell eingeben")
        layout.addWidget(self.custom_input)

        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Übernehmen")
        save_btn.clicked.connect(self.accept)

        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def get_selected_name(self):
        """Gibt den ausgewählten oder manuell eingegebenen Modulnamen zurück."""
        # Eine manuelle Eingabe hat Vorrang vor Auswahl aus dem Katalog.
        custom_val = self.custom_input.text().strip()
        if custom_val:
            return custom_val
        sel = self.tree.selectedItems()
        if sel and sel[0].parent():
            return sel[0].data(0, Qt.ItemDataRole.UserRole)
        return ""


class AddTodoDialog(QDialog):
    """Dialogfenster zum Erstellen einer neuen To-Do-Aufgabe."""

    def __init__(self, modules, parent=None):
        """Initialisiert den Aufgabendialog."""
        super().__init__(parent)
        self.setWindowTitle("Neue Aufgabe anlegen")
        self.setFixedWidth(420)

        self.validated_due_date = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("z. B. Praktikumsprotokoll abgeben")
        form_layout.addRow("Titel:", self.title_input)

        self.module_combo = QComboBox()
        # Der leere Modulcode steht für eine Aufgabe ohne Modulzuordnung.
        self.module_combo.addItem("Allgemein", "")
        for m in modules:
            self.module_combo.addItem(f"{m.code} - {m.name}", m.code)
        form_layout.addRow("Modul:", self.module_combo)

        self.due_input = QLineEdit()
        # Als Vorschlag wird zunächst das heutige Datum eingesetzt.
        self.due_input.setText(datetime.now().strftime("%d.%m.%Y"))
        self.due_input.setPlaceholderText("TT.MM.JJJJ (optional)")
        form_layout.addRow("Frist:", self.due_input)

        layout.addLayout(form_layout)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: red; font-weight: bold;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        layout.addWidget(self.error_lbl)

        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Hinzufügen")
        save_btn.clicked.connect(self._on_save_clicked)

        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _on_save_clicked(self):
        """Prüft Titel und Frist-Datum auf Gültigkeit."""
        title = self.title_input.text().strip()
        if not title:
            self.error_lbl.setText("Bitte gib einen Titel für die Aufgabe ein.")
            self.error_lbl.show()
            return

        due_raw = self.due_input.text().strip()
        # Nur ein gültiges oder leeres Datum darf gespeichert werden.
        ok, res = validate_due_date(due_raw)
        if not ok:
            self.error_lbl.setText(res)
            self.error_lbl.show()
            return

        self.error_lbl.hide()
        self.validated_due_date = res
        self.accept()

    def get_todo_data(self):
        """Gibt Titel, verknüpftes Modul und die geprüfte Frist zurück."""
        return self.title_input.text().strip(), self.module_combo.currentData(), self.validated_due_date
