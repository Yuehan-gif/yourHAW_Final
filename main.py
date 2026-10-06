# main.py - Startpunkt der App
# Entwickelt von Johann, Dennis, Janina und Leon (HAW Hamburg, Medientechnik)

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

from models import StudyPlan
from services import load_curriculum, save_user_data, load_user_data
from gui import MainWindow, CURRICULUM_PATH, USER_PROGRESS_PATH


def erzwinge_light_mode(app):
    """Erzwingt helle Farben/Farbprofil des Programms damit es auf jedem System gleich aussieht."""
    # Fusion-Style aktivieren und helle Farbpalette setzen (sonst übernimmt Windows/macOS die System-Farben)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 233, 233))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def main():
    """Startet die Anwendung."""
    # Anwendung starten und gespeicherte Daten laden
    app = QApplication(sys.argv)
    app.setApplicationName("Your HAW - Studienplaner")

    # Heller Modus für einheitlichen Look
    erzwinge_light_mode(app)

    # Gespeicherten Stand laden oder beim ersten Mal neuen Plan anlegen
    plan = load_user_data(USER_PROGRESS_PATH)
    if not plan:
        base_modules = load_curriculum(CURRICULUM_PATH) or []
        plan = StudyPlan(
            student_name="",
            start_semester="SoSe",
            start_year=2025,
            modules=base_modules,
            todos=[],
            birth_date="",
            setup_completed=False,
        )
        save_user_data(plan, USER_PROGRESS_PATH)

    # Hauptfenster öffnen (startet direkt auf dem Dashboard wenn schon eingerichtet, sonst Willkommensseite)
    window = MainWindow(plan)
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
