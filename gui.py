# gui.py - Hauptansicht mit Dashboard, Aufgaben, Übersicht und Prognosen
# Geschrieben von Leon (HAW Medientechnik)

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QTabWidget,
    QLabel,
    QPushButton,
    QProgressBar,
    QComboBox,
    QDialog,
    QMessageBox,
    QFrame,
    QScrollArea,
    QCheckBox,
    QGroupBox,
    QRadioButton,
)

from models import StudyPlan, Module, TodoItem
from services import (
    load_curriculum,
    save_user_data,
    calculate_ects_summary,
    calculate_timeline,
    calculate_electives_summary,
    calculate_age_at_date,
    CURRICULUM_PATH,
    USER_PROGRESS_PATH,
)
from setup_views import (
    IntroScreen,
    SetupStep1Screen,
    SetupStep2Screen,
    EditModuleDialog,
    SelectElectiveFromCatalogDialog,
    AddTodoDialog,
)


class MainAppView(QWidget):
    """Hauptansicht der Anwendung"""

    def __init__(self, plan, on_navigate_intro=None, on_reset_callback=None, parent=None):
        """Initialisiert die Hauptansicht und baut die Tab-Struktur auf."""
        super().__init__(parent)
        self.plan = plan
        self.on_navigate_intro = on_navigate_intro
        self.on_reset_callback = on_reset_callback

        # Das äußere Layout ordnet Kopfzeile und Registerkarten untereinander an.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        app_title = QLabel("Your HAW - Studienplaner Medientechnik (B.Sc.)")
        app_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_box.addWidget(app_title)

        self.user_lbl = QLabel("")
        title_box.addWidget(self.user_lbl)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Ermöglicht Wechsel zwischen den vier Bereichen der Anwendung.
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget, 1)

        self.tab_dashboard = self._build_dashboard_tab()
        self.tab_tasks = self._build_tasks_tab()
        self.tab_overview = self._build_overview_tab()
        self.tab_prognosen = self._build_prognosen_tab()

        self.tab_widget.addTab(self.tab_dashboard, "Dashboard")
        self.tab_widget.addTab(self.tab_tasks, "Aufgaben")
        self.tab_widget.addTab(self.tab_overview, "Übersicht")
        self.tab_widget.addTab(self.tab_prognosen, "Prognosen")

        self.refresh_all()

    def _build_dashboard_tab(self):
        """Baut den Dashboard-Tab mit Fortschritt, Kennzahlen und Punkteverteilung auf."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        progress_group = QGroupBox("Dein Studienfortschritt")
        p_lay = QVBoxLayout(progress_group)
        p_lay.setContentsMargins(10, 12, 10, 12)
        p_lay.setSpacing(8)

        self.dash_bar = QProgressBar()
        self.dash_bar.setRange(0, 210)
        self.dash_bar.setFixedHeight(26)
        self.dash_bar.setFormat("%v / %m ECTS (%p%)")
        p_lay.addWidget(self.dash_bar)

        layout.addWidget(progress_group)

        stats_group = QGroupBox("Wichtige Kennzahlen")
        s_lay = QHBoxLayout(stats_group)
        s_lay.setSpacing(15)
        s_lay.setContentsMargins(12, 12, 12, 12)

        col_ects = QVBoxLayout()
        col_ects.setSpacing(2)
        col_ects.addWidget(QLabel("ECTS-PUNKTE"))
        self.dash_points_val = QLabel("0 ECTS")
        self.dash_points_val.setStyleSheet("font-size: 22px; font-weight: bold; color: green;")
        col_ects.addWidget(self.dash_points_val)
        self.dash_points_desc = QLabel("210 ECTS Regelbedarf")
        col_ects.addWidget(self.dash_points_desc)
        s_lay.addLayout(col_ects, 1)

        col_grade = QVBoxLayout()
        col_grade.setSpacing(2)
        col_grade.addWidget(QLabel("NOTENDURCHSCHNITT"))
        self.dash_grade_val = QLabel("-.-")
        self.dash_grade_val.setStyleSheet("font-size: 22px; font-weight: bold;")
        col_grade.addWidget(self.dash_grade_val)
        self.dash_grade_desc = QLabel("Gewichteter Durchschnitt")
        col_grade.addWidget(self.dash_grade_desc)
        s_lay.addLayout(col_grade, 1)

        col_mods = QVBoxLayout()
        col_mods.setSpacing(2)
        col_mods.addWidget(QLabel("MODULE & LABORE"))
        self.dash_mods_val = QLabel("0 / 50")
        self.dash_mods_val.setStyleSheet("font-size: 22px; font-weight: bold;")
        col_mods.addWidget(self.dash_mods_val)
        self.dash_mods_desc = QLabel("Leistungen bestanden")
        col_mods.addWidget(self.dash_mods_desc)
        s_lay.addLayout(col_mods, 1)

        layout.addWidget(stats_group)

        dist_group = QGroupBox("Punkteverteilung im Bachelor (210 ECTS Gesamt)")
        d_lay = QGridLayout(dist_group)
        d_lay.setSpacing(8)

        # Erklärung, wie sich die 210 ECTS zusammensetzen.
        items = [
            ("Pflichtmodule (Semester 1-6)", "145 ECTS", "Vorlesungen, Übungen und Klausuren"),
            ("Wahlpflichtfächer (WPF)", "35 ECTS", "7 Module (mind. 4x Technik, mind. 2x Gestaltung)"),
            ("Praxisphase (7. Semester)", "15 ECTS", "Betriebspraktikum / Praxisphase laut Studienplan"),
            ("Bachelorarbeit & Kolloquium (7. Sem.)", "15 ECTS", "12 ECTS Bachelorarbeit + 3 ECTS Kolloquium"),
        ]

        for row_idx, (title_str, ects_str, desc_str) in enumerate(items):
            d_lay.addWidget(QLabel(f"• {title_str}"), row_idx, 0)
            e_lbl = QLabel(ects_str)
            e_lbl.setStyleSheet("font-weight: bold;")
            d_lay.addWidget(e_lbl, row_idx, 1)
            d_lay.addWidget(QLabel(desc_str), row_idx, 2)

        layout.addWidget(dist_group)
        layout.addStretch()
        return tab

    def refresh_dashboard(self):
        """Aktualisiert alle Kennzahlen und Balken auf dem Dashboard."""
        summary = calculate_ects_summary(self.plan)
        passed_cnt = sum(1 for m in self.plan.modules if m.passed)
        total_cnt = len(self.plan.modules)
        ects_done = summary["ects_completed"]
        ects_tot = summary["ects_total"]
        rem = summary["ects_remaining"]
        gpa = summary["weighted_gpa"]

        self.dash_bar.setValue(ects_done)
        self.dash_points_val.setText(f"{ects_done} ECTS")
        self.dash_points_desc.setText(f"{rem} ECTS verbleibend von {ects_tot}")

        # Solange keine benotete Leistung vorliegt, gibt es keinen Durchschnitt.
        if gpa is not None:
            self.dash_grade_val.setText(f"{gpa:.2f}")
            self.dash_grade_desc.setText("Gewichteter Durchschnitt")
        else:
            self.dash_grade_val.setText("-.-")
            self.dash_grade_desc.setText("Noch keine benoteten Fächer")

        self.dash_mods_val.setText(f"{passed_cnt} / {total_cnt}")
        self.dash_mods_desc.setText(f"{passed_cnt} von {total_cnt} Leistungen bestanden")

    def _build_tasks_tab(self):
        """Baut Aufgaben-Tab zur Verwaltung persönlicher To-Dos auf."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Filter:"))
        self.task_filter = QComboBox()
        self.task_filter.addItems(["Alle Aufgaben", "Nur offene", "Nur erledigte"])
        self.task_filter.currentIndexChanged.connect(self.refresh_tasks)
        top_bar.addWidget(self.task_filter)

        top_bar.addStretch()

        add_btn = QPushButton("Aufgabe hinzufügen +")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_task)
        top_bar.addWidget(add_btn)

        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.StyledPanel)

        container = QWidget()
        self.tasks_list_layout = QVBoxLayout(container)
        self.tasks_list_layout.setSpacing(6)
        self.tasks_list_layout.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        return tab

    def refresh_tasks(self):
        """Erneuert die Anzeige der Aufgabenliste basierend auf gewähltem Filter."""
        # Vor dem Neuaufbau werden die bisherigen Widgets aus dem Layout entfernt.
        while self.tasks_list_layout.count():
            item = self.tasks_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filter_idx = self.task_filter.currentIndex()
        filtered = []
        # Ausgewählter Filter entscheidet, welche Aufgaben angezeigt werden.
        for t in self.plan.todos:
            if filter_idx == 1 and t.is_done:
                continue
            if filter_idx == 2 and not t.is_done:
                continue
            filtered.append(t)

        if not filtered:
            lbl = QLabel("Keine Aufgaben vorhanden. Klicke oben auf 'Aufgabe hinzufügen +'.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_list_layout.addWidget(lbl)
            self.tasks_list_layout.addStretch()
            return

        for todo in filtered:
            row_w = QWidget()
            r_lay = QHBoxLayout(row_w)
            r_lay.setContentsMargins(6, 4, 6, 4)
            r_lay.setSpacing(10)

            chk = QCheckBox()
            chk.setChecked(todo.is_done)
            chk.stateChanged.connect(lambda state, t=todo: self._toggle_task(t))
            r_lay.addWidget(chk)

            t_box = QVBoxLayout()
            t_box.setSpacing(2)

            t_title = QLabel(todo.title)
            if todo.is_done:
                t_title.setStyleSheet("text-decoration: line-through; color: gray;")
            else:
                t_title.setStyleSheet("font-weight: bold;")
            t_box.addWidget(t_title)

            due_txt = f"Modul: {todo.module_code or 'Allgemein'}"
            if todo.due_date:
                due_txt += f" | Frist: {todo.due_date}"
            t_box.addWidget(QLabel(due_txt))

            r_lay.addLayout(t_box, 1)

            del_btn = QPushButton("Löschen")
            del_btn.setFixedWidth(70)
            # ID wird beim Erzeugen des Buttons gespeichert, damit die richtige Aufgabe gelöscht wird.
            del_btn.clicked.connect(lambda checked=False, tid=todo.task_id: self._del_task(tid))
            r_lay.addWidget(del_btn)

            self.tasks_list_layout.addWidget(row_w)

        self.tasks_list_layout.addStretch()

    def _on_add_task(self):
        """Öffnet Fenster zum Hinzufügen einer neuen Aufgabe."""
        dlg = AddTodoDialog(self.plan.modules, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, mod, due = dlg.get_todo_data()
            if not title:
                return
            nid = max([t.task_id for t in self.plan.todos], default=0) + 1
            self.plan.add_todo(TodoItem(task_id=nid, title=title, module_code=mod, due_date=due))
            save_user_data(self.plan, USER_PROGRESS_PATH)
            self.refresh_tasks()

    def _toggle_task(self, todo):
        """Wechselt den Status einer Aufgabe und speichert dieses."""
        todo.toggle_status()
        save_user_data(self.plan, USER_PROGRESS_PATH)
        self.refresh_tasks()

    def _del_task(self, tid):
        """Löscht eine Aufgabe aus dem Studienplan."""
        self.plan.remove_todo(tid)
        save_user_data(self.plan, USER_PROGRESS_PATH)
        self.refresh_tasks()

    def _build_overview_tab(self):
        """Baut Übersichts-Tab mit Spaltenansicht und Zeitleiste auf."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        mode_bar = QHBoxLayout()
        mode_bar.addWidget(QLabel("Ansicht wählen:"))

        self.btn_spalten = QRadioButton("Spaltenansicht (Semester 1-7)")
        self.btn_spalten.setChecked(True)
        self.btn_spalten.toggled.connect(self._on_view_mode_changed)
        mode_bar.addWidget(self.btn_spalten)

        self.btn_timeline = QRadioButton("Zeitleiste")
        self.btn_timeline.toggled.connect(self._on_view_mode_changed)
        mode_bar.addWidget(self.btn_timeline)

        mode_bar.addStretch()
        layout.addLayout(mode_bar)

        # Spaltenansicht und Zeitleiste auf derselben Fläche.
        self.sub_stack = QStackedWidget()
        layout.addWidget(self.sub_stack, 1)

        self.scroll_sp = QScrollArea()
        self.scroll_sp.setWidgetResizable(True)
        self.scroll_sp.setFrameShape(QFrame.Shape.StyledPanel)
        self.scroll_sp.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_sp.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.cont_sp = QWidget()
        self.spalten_lay = QHBoxLayout(self.cont_sp)
        self.spalten_lay.setContentsMargins(8, 8, 8, 12)
        self.spalten_lay.setSpacing(12)
        self.scroll_sp.setWidget(self.cont_sp)
        self.sub_stack.addWidget(self.scroll_sp)

        self.scroll_tl = QScrollArea()
        self.scroll_tl.setWidgetResizable(True)
        self.scroll_tl.setFrameShape(QFrame.Shape.StyledPanel)
        self.scroll_tl.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        cont_tl = QWidget()
        self.timeline_lay = QVBoxLayout(cont_tl)
        self.timeline_lay.setSpacing(10)
        self.timeline_lay.setContentsMargins(8, 8, 8, 8)
        self.scroll_tl.setWidget(cont_tl)
        self.sub_stack.addWidget(self.scroll_tl)

        return tab

    def _on_view_mode_changed(self):
        """Wechselt zwischen Spalten- und Zeitleistenansicht."""
        # Index 0 ist die Spaltenansicht, Index 1 die Zeitleiste
        if self.btn_spalten.isChecked():
            self.sub_stack.setCurrentIndex(0)
        else:
            self.sub_stack.setCurrentIndex(1)

    def refresh_overview(self):
        """Aktualisiert Spaltenansicht und Zeitleiste komplett."""
        # Die Semesteransicht wird aus dem aktuellen Datenstand vollständig neu aufgebaut.
        while self.spalten_lay.count():
            item = self.spalten_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        col_width = 270
        for sem in range(1, 8):
            col_box = QGroupBox(f"{sem}. Semester")
            col_box.setFixedWidth(col_width)
            c_lay = QVBoxLayout(col_box)
            c_lay.setSpacing(6)
            c_lay.setContentsMargins(6, 10, 6, 6)

            sem_mods = [m for m in self.plan.modules if m.semester == sem]
            for m in sem_mods:
                m_btn = QPushButton()
                m_btn.setCursor(Qt.CursorShape.PointingHandCursor)

                status_txt = f"Bestanden (Note {m.grade})" if (m.passed and m.grade) else ("Bestanden" if m.passed else "Offen")
                m_btn.setText(f"{m.code}: {m.name}\n[{status_txt} - {m.ects} ECTS]")

                if m.passed:
                    m_btn.setStyleSheet("background-color: #c8e6c9; text-align: left;")
                else:
                    m_btn.setStyleSheet("text-align: left;")

                m_btn.clicked.connect(lambda checked=False, mod=m: self._on_edit_mod(mod))
                c_lay.addWidget(m_btn)
                # mod=m verhindert, dass später alle Buttons auf das letzte Modul zeigen.

            c_lay.addStretch()
            self.spalten_lay.addWidget(col_box)

        self.spalten_lay.addStretch()
        self.cont_sp.setMinimumWidth(7 * col_width + (6 * 12) + 40)

        while self.timeline_lay.count():
            item = self.timeline_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tl = calculate_timeline(self.plan)
        # Der Service bestimmt anhand des Studienbeginns das aktuelle Fachsemester
        cur_sem = tl["current_fachsemester"]

        for sem in range(1, 8):
            is_cur = (sem == cur_sem)
            sem_mods = [m for m in self.plan.modules if m.semester == sem]
            passed_mods = [m for m in sem_mods if m.passed]
            passed_count = len(passed_mods)
            total_count = len(sem_mods)
            passed_ects = sum(m.ects for m in passed_mods)
            total_ects = sum(m.ects for m in sem_mods)

            box_title = f"{sem}. Semester"
            if is_cur:
                box_title += f" (Aktuelles Semester - Stand: {datetime.now().strftime('%d.%m.%Y')})"

            sem_box = QGroupBox(box_title)

            sb_lay = QVBoxLayout(sem_box)
            sb_lay.setSpacing(6)

            info_line = f"Fortschritt: {passed_count}/{total_count} Leistungen bestanden ({passed_ects}/{total_ects} ECTS)"
            lbl_info = QLabel(info_line)
            lbl_info.setStyleSheet("font-weight: bold;")
            sb_lay.addWidget(lbl_info)

            mod_texts = []
            for m in sem_mods:
                icon_str = "[x] " if m.passed else "[ ] "
                mod_texts.append(f"{icon_str}{m.code} {m.name} ({m.ects} ECTS)")

            lbl_mods = QLabel("   |   ".join(mod_texts))
            lbl_mods.setWordWrap(True)
            sb_lay.addWidget(lbl_mods)

            self.timeline_lay.addWidget(sem_box)

        self.timeline_lay.addStretch()

    def _on_edit_mod(self, mod):
        """Zeigt Auswahl- oder Bearbeitungsdialog für ein Modul."""
        # Bei Wahlpflichtmodulen kann ein konkretes Fach ausgewählt werden
        if mod.is_elective:
            msg = QMessageBox(self)
            msg.setWindowTitle(f"Wahlpflichtfach: {mod.code}")
            msg.setText(f"Was möchtest du für {mod.code} ({mod.name}) tun?")
            btn_choose = msg.addButton("WPF wählen / umbenennen", QMessageBox.ButtonRole.ActionRole)
            btn_grade = msg.addButton("Note / Status bearbeiten", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked == btn_choose:
                self._on_choose_wpf(mod)
            elif clicked == btn_grade:
                self._do_edit_mod_dialog(mod)
        else:
            self._do_edit_mod_dialog(mod)

    def _do_edit_mod_dialog(self, mod):
        """Öffnet den Bearbeitungsdialog für ein konkretes Modul."""
        dlg = EditModuleDialog(mod, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply_changes()
            save_user_data(self.plan, USER_PROGRESS_PATH)
            self.refresh_all()

    def _on_choose_wpf(self, mod):
        """Öffnet den Dialog zur Wahlpflichtfach-Auswahl aus dem Katalog."""
        dlg = SelectElectiveFromCatalogDialog(mod, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            chosen = dlg.get_selected_name()
            if chosen:
                mod.rename(chosen)
                save_user_data(self.plan, USER_PROGRESS_PATH)
                self.refresh_all()

    def _build_prognosen_tab(self):
        """Baut den Prognosen-Tab mit Semesterberechnungen und Reset-Funktion auf."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(12)

        left_group = QGroupBox("Voraussichtlicher Abschluss")
        l_lay = QVBoxLayout(left_group)
        l_lay.setSpacing(8)

        l_lay.addWidget(QLabel("<b>Errechnetes Abschlussdatum:</b>"))

        self.p_end_date = QLabel("28.07.2028")
        self.p_end_date.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.p_end_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_lay.addWidget(self.p_end_date)

        self.p_end_date_hint = QLabel("")
        self.p_end_date_hint.setWordWrap(True)
        l_lay.addWidget(self.p_end_date_hint)

        l_lay.addSpacing(6)
        l_lay.addWidget(QLabel("<b>Voraussichtliches Alter beim Abschluss:</b>"))

        self.p_age = QLabel("26")
        self.p_age.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.p_age.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_lay.addWidget(self.p_age)

        self.p_age_hint = QLabel("")
        self.p_age_hint.setWordWrap(True)
        l_lay.addWidget(self.p_age_hint)

        l_lay.addStretch()
        row.addWidget(left_group, 1)

        right_group = QGroupBox("Regelstudienzeit & Kennzahlen")
        r_lay = QVBoxLayout(right_group)
        r_lay.setSpacing(6)

        self.p_sem = QLabel("Aktuelles Fachsemester: -")
        self.p_regel = QLabel("Regelstudienzeit-Ende: -")
        self.p_days = QLabel("Verbleibende Tage bis Regelende: -")
        self.p_pace = QLabel("Aktuelles Tempo: -")
        self.p_sem_left = QLabel("Benötigte Semester: -")
        self.p_wpf = QLabel("Wahlpflichtfächer: -")

        for lbl in (self.p_sem, self.p_regel, self.p_days, self.p_pace, self.p_sem_left, self.p_wpf):
            r_lay.addWidget(lbl)

        r_lay.addStretch()
        row.addWidget(right_group, 1)

        layout.addLayout(row)

        reset_group = QGroupBox("Studienplan zurücksetzen")
        rg_lay = QHBoxLayout(reset_group)
        rg_lay.setSpacing(10)

        desc_box = QVBoxLayout()
        desc_box.setSpacing(2)
        desc_box.addWidget(QLabel("<b>Studienplan und Ersteinrichtung zurücksetzen</b>"))
        desc_box.addWidget(QLabel("Löscht alle erfassten Noten, Daten und Aufgaben und startet den Einrichtungsassistenten neu."))
        rg_lay.addLayout(desc_box, 1)

        reset_btn = QPushButton("Alles zurücksetzen")
        reset_btn.setFixedHeight(32)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._on_reset_btn_clicked)
        rg_lay.addWidget(reset_btn)

        layout.addWidget(reset_group)
        layout.addStretch()
        return tab

    def _on_reset_btn_clicked(self):
        """Zeigt Sicherheitsabfrage zum Zurücksetzen des Studienplans."""
        reply = QMessageBox.question(
            self,
            "Studienplan zurücksetzen?",
            "Möchtest du wirklich alle eingetragenen Daten und Noten löschen und das Setup von vorne beginnen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.on_reset_callback:
                self.on_reset_callback()

    def refresh_prognosen(self):
        """Aktualisiert alle Werte im Prognosen-Tab."""
        # Zeit- und Wahlpflichtberechnung sind von der Darstellung getrennt.
        tl = calculate_timeline(self.plan)
        wpf = calculate_electives_summary(self.plan)

        pred_date = tl["predicted_end_date"]
        self.p_end_date.setText(pred_date)
        self.p_end_date_hint.setText(f"Basis: {tl.get('calculation_basis', 'Regelstudienzeit')}")

        birth = getattr(self.plan, "birth_date", "").strip()
        age = calculate_age_at_date(birth, pred_date)
        if age is not None:
            self.p_age.setText(f"{age} Jahre")
            self.p_age_hint.setText(f"Berechnet aus Geburtsdatum ({birth}) zum Abschluss ({pred_date})")
        else:
            self.p_age.setText("-")
            self.p_age_hint.setText("Kein Geburtsdatum hinterlegt")

        self.p_sem.setText(f"Aktuelles Fachsemester: {tl['current_fachsemester']}. Semester")
        self.p_regel.setText(f"Regelstudienzeit-Ende: {tl['regel_end_term']} ({tl['regel_end_date']})")
        self.p_days.setText(f"Verbleibende Tage: {tl['remaining_days_regel']} Tage")
        self.p_pace.setText(f"Aktuelles Tempo: {tl['pace_ects_per_sem']} ECTS / Semester")
        self.p_sem_left.setText(f"Benötigte Semester: ca. {tl['remaining_semesters_needed']} Semester")
        self.p_wpf.setText(f"Wahlpflichtfächer: {wpf['completed_electives']}/7 (Technik: {wpf['technik_count']}/4, Gestaltung: {wpf['gestaltung_count']}/2)")

    def refresh_all(self):
        """Aktualisiert die gesamte Nutzeroberfläche nach Datenänderungen."""
        user_name = self.plan.student_name.strip() if self.plan.student_name else ""
        if user_name:
            user_sub = f"Studierende/r: {user_name} | Start: {self.plan.start_semester} {self.plan.start_year}"
        else:
            user_sub = "Noch nicht eingerichtet"
        self.user_lbl.setText(user_sub)

        self.refresh_dashboard()
        self.refresh_tasks()
        self.refresh_overview()
        self.refresh_prognosen()


class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung, verwaltet die Grundansicht/-layout der Ansichten."""

    def __init__(self, plan):
        """Initialisiert das Hauptfenster und seine untergeordneten Ansichten."""
        super().__init__()
        self.plan = plan
        self.setWindowTitle("Your HAW - Medientechnik Studienplaner")
        self.resize(1100, 780)

        # Der Hauptstapel enthält Intro, zwei Setup Seiten und die eigentliche Anwendung.
        # Sichtbar ist immer nur die Seite mit dem aktuell gewählten Index.
        self.master_stack = QStackedWidget()
        self.setCentralWidget(self.master_stack)

        self.intro_screen = IntroScreen(on_start_callback=self._on_start_clicked)
        self.master_stack.addWidget(self.intro_screen)

        self.step1_screen = SetupStep1Screen(
            self.plan,
            on_next=lambda: self.master_stack.setCurrentIndex(2),
            on_cancel=self._on_setup_cancelled,
        )
        self.master_stack.addWidget(self.step1_screen)

        self.step2_screen = SetupStep2Screen(
            self.plan,
            on_back=lambda: self.master_stack.setCurrentIndex(1),
            on_finish=self._on_setup_finished,
        )
        self.master_stack.addWidget(self.step2_screen)

        self.main_app_view = MainAppView(
            self.plan,
            on_navigate_intro=lambda: self.master_stack.setCurrentIndex(0),
            on_reset_callback=self._on_reset_app,
        )
        self.master_stack.addWidget(self.main_app_view)

        # Nach abgeschlossener Einrichtung kann die Startsequenz übersprungen werden.
        if self.plan.is_setup_done():
            self.master_stack.setCurrentIndex(3)
        else:
            self.master_stack.setCurrentIndex(0)

    def _on_start_clicked(self):
        """Wechselt von der Willkommensseite zu Schritt 1 des Setups."""
        self.master_stack.setCurrentIndex(1)

    def _on_setup_cancelled(self):
        """Bricht die Einrichtung ab und schaltet zur Hauptansicht oder Intro zurück."""
        if self.plan.is_setup_done():
            self.master_stack.setCurrentIndex(3)
        else:
            self.master_stack.setCurrentIndex(0)

    def _on_setup_finished(self):
        """Schließt die Ersteinrichtung ab und schaltet zum Haupt-Dashboard."""
        # Der gespeicherte Status sorgt dafür, dass das Setup nur einmal erscheint
        self.plan.setup_completed = True
        save_user_data(self.plan, USER_PROGRESS_PATH)
        self.main_app_view.refresh_all()
        self.master_stack.setCurrentIndex(3)

    def _on_reset_app(self):
        """Setzt die gesamte Anwendung und alle Nutzerdaten zurück."""
        # Beim Zurücksetzen werden die unveränderten Module aus dem Katalog neu geladen.
        fresh_modules = load_curriculum(CURRICULUM_PATH) or []
        self.plan.student_name = ""
        self.plan.birth_date = ""
        self.plan.start_semester = "SoSe"
        self.plan.start_year = 2025
        self.plan.setup_completed = False
        self.plan.modules = fresh_modules
        self.plan.todos.clear()

        save_user_data(self.plan, USER_PROGRESS_PATH)

        self.step1_screen.reset_fields()
        self.step2_screen.refresh_columns()
        self.main_app_view.refresh_all()
        self.master_stack.setCurrentIndex(0)
