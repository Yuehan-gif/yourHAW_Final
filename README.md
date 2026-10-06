# Your HAW – Medientechnik Studienplaner & Prognosetool (B.Sc.)

Semesterprojekt der **Hochschule für Angewandte Wissenschaften Hamburg (HAW Hamburg)**  
**Fakultät DMI** (Design, Medien, Information) – **Department Medientechnik**  
Bachelor of Science

---

## 1. Das Projekt

Im Rahmen unseres Softwareprojekts (Programmieren 1) haben wir zu viert eine leicht verständliche, 100% lokale Desktop-App entwickelt, mit der Medientechnik-Studierende ihren Studienverlauf interaktiv planen und nachverfolgen können.

### Team & Aufgabenverteilung 
- **Johann Schröger**: `models.py` – Datenklassen für Fächer, Aufgaben und Studienplan (`Module`, `TodoItem`, `StudyPlan`).
- **Dennis Vorwerk**: `services.py` – Berechnungen (ECTS-Zähler, Notenschnitt, Zeitprognosen) und Geburtsdatum-Validierung.
- **Janina Meißner**: `setup_views.py` – Startbildschirm, Onboarding (Schritt 1 Daten & Schritt 2 Vorleistungen) und Dialoge.
- **Leon Paul**: `gui.py` – Hauptansicht mit den 4 Reitern (Dashboard, Aufgaben, Übersicht und Prognosen).
- **Gemeinsam**: `main.py` – Startskript für die App.

---

## 2. Projektstruktur 

```
HAW progress/
├── data/
│   ├── modules_medientechnik.json  # Medientechnik-Curriculum (210 ECTS, 7 Semester)
│   ├── electives_catalog.json      # HAW Wahlpflichtkatalog (Technik & Gestaltung)
│   └── user_progress.json         # Lokaler Speicherstand
│
├── tests/
│   ├── test_models.py             # Tests für Datenmodelle & To-Dos
│   └── test_services.py           # Tests für ECTS, Noten, Alter & Zeitrechnung
│
├── main.py                        # Startskript: Startet die Qt-Anwendung
├── models.py                      # Johann: Datenstrukturen (Module, StudyPlan, TodoItem)
├── services.py                    # Dennis: Berechnungen, Logik & Geburtsdatum-Check
├── setup_views.py                 # Janina: Onboarding-Screens & Dialoge
├── gui.py                         # Leon: Hauptansicht & Navigation
├── start.bat                      # 1-Klick-Starter für Windows
├── requirements.txt               # Externe Python-Pakete (PyQt6, pytest)
└── README.md                      # Projektdokumentation
```

---

## 3. Funktionsübersicht

1. **Intro & Einrichtung (Schritt 1 & 2)**:
   - Startscreen mit Begrüßung.
   - Dateneingabe von Name, Geburtsdatum und Studienbeginn (SoSe / WiSe).
   - Schnelle Eingabe von bereits erbrachter Listungen nach Semestern geordnet.
2. **Dashboard ("Mein Studienfortschritt")**:
   - Fortschrittsbalken über alle 210 ECTS.
   - Kennzahlen (ECTS, offene Labore, gewichteter Schnitt).
3. **Meine Aufgaben (Tasks)**:
   - Modulbezogene To-Do-Liste mit Fälligkeitsdatum und Status-Checkboxen.
4. **Übersicht (Spalten & Zeitleiste)**:
   - *Spaltenansicht*: Horizontale Ansicht aller 7 Semester nebeneinander.
   - *Zeitleiste*: Vertikaler Zeitstrahl mit Semester-Fortschritt und Modulauflistung.
5. **Prognosen & Altersrechner**:
   - Voraussichtlicher Studienabschluss (z.B. 28.07.2028).
   - Altersanzeige zum Zeitpunkt des Abschlusses ("Du bist dann 26").
   - Transparente Erklärungsgrundlage (Regelstudienzeit vs. persönliches ECTS-Tempo).

---

## 4. Installation & Start

### Voraussetzungen
- Python 3.10 oder neuere Version (getestet mit Python 3.13 und 3.14).

### Starten unter Windows
Über das Terminal:

```
python main.py
```

---

## 5. Automatisierte Tests ausführen

```
python -m pytest
```
