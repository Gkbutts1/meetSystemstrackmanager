import os
import sqlite3
import platform  # Import platform to detect OS
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog, QMessageBox, QDateEdit
from PyQt6.QtCore import QDate

def create_table(cursor, table_name, columns):
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
    cursor.execute(query)

def create_database(file_path, use_age_group_birthday, meet_date):
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        create_table(cursor, 'athletes', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            team_code STRING,
            team_name STRING,
            last_name STRING,
            first_name STRING,
            middle_initials STRING,
            dob DATETIME,
            gender STRING,
            bib_number INTEGER,
            membership_number STRING
        ''')

        create_table(cursor, 'teams', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            team_code TEXT
        ''')

        cursor.execute("""
            INSERT INTO teams (team_name, team_code)
            VALUES (?, ?)
        """, ("Unattached", "UNA"))

        # divisions age group
        create_table(cursor, 'divisions_age_group', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division_number INTEGER,
            division_abbr STRING,
            division_name STRING,
            from_age INTEGER,
            to_age INTEGER, 
            age_as_of_date DATETIME
        ''')
        # divisions non  age group
        create_table(cursor, 'divisions_non_age_groups', '''
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    division_number integer,
                    division_abbr STRING,
                    division_name STRING

                ''')

        # # Events table
        # create_table(cursor, 'events', '''
        #     event_number INTEGER NOT NULL,
        #     event_name TEXT NOT NULL,
        #     division_name TEXT NOT NULL,
        #     gender TEXT NOT NULL,
        #     event_type TEXT,
        #     event_rounds INTEGER,
        #     event_lanes_position INTEGER
        #
        # ''')
        # Events table
        create_table(cursor, 'events', '''
                    event_number INTEGER ,
                    seeding TEXT  ,
                    gender TEXT ,
                    division_name TEXT ,
                    event_name TEXT  ,
                    number_of_rounds INTEGER ,
                    round_names TEXT  ,
                    number_of_lanes INTEGER DEFAULT 8, -- Default value set to 8
                    advancement TEXT

                ''')



        create_table(cursor, 'settings', '''
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT,
            setting_meet_date DATETIME,
            setting_row_count INTEGER
        ''')

        # Insert the settings including the meet date
        cursor.execute("INSERT INTO settings (setting_name, setting_value, setting_meet_date,setting_row_count) VALUES (?, ?, ? ,?)",
                       ('use_age_group_birthday', str(use_age_group_birthday), meet_date,int(4)))

        conn.commit()
        conn.close()
        print(f"Database created successfully at: {file_path}")

    except sqlite3.Error as e:
        print(f"Failed to create database: {e}")
        QMessageBox.critical(None, "Database Error", f"Failed to create the database: {e}")


class MeetSetupDialog(QDialog):
    def __init__(self, parent=None):
        super(MeetSetupDialog, self).__init__(parent)
        self.setWindowTitle("Meet Setup")
        self.setGeometry(100, 100, 300, 200)
        self.layout = QVBoxLayout()

        self.meet_name_label = QLabel("Meet Name:")
        self.layout.addWidget(self.meet_name_label)

        self.meet_name_entry = QLineEdit()
        self.layout.addWidget(self.meet_name_entry)

        self.meet_date_label = QLabel("Meet Date:")
        self.layout.addWidget(self.meet_date_label)

        self.meet_date_entry = QDateEdit()
        self.meet_date_entry.setCalendarPopup(True)
        self.meet_date_entry.setDate(QDate.currentDate())  # Set default to current date
        self.layout.addWidget(self.meet_date_entry)

        self.age_group_checkbox = QCheckBox("Use Age Group Birthday?")
        self.layout.addWidget(self.age_group_checkbox)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_meet_name)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def submit_meet_name(self):
        meet_name = self.meet_name_entry.text().strip()
        if not meet_name:
            QMessageBox.critical(self, "Error", "Meet Name is required")
            return

        # use_age_group_birthday = self.age_group_checkbox.isChecked()
        # meet_date = self.meet_date_entry.date().toString("yyyy-MM-dd")  # Format date to string for SQLite
        use_age_group_birthday = self.age_group_checkbox.isChecked()
        meet_date = self.meet_date_entry.date().toString("MM/dd/yyyy")  # Format date to 'MM-dd-yyyy' for SQLite

        # Detect the operating system and set the folder path accordingly
        if platform.system() == "Windows":
            folder_path = r"C:\MeetSystems"
        elif platform.system() == "Darwin":  # Darwin is the system name for macOS
            folder_path = os.path.expanduser("~/Documents/MeetSystems")
        else:
            QMessageBox.critical(self, "Error", "Unsupported Operating System")
            return

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database",
            os.path.join(folder_path, f"{meet_name}.db"),
            "SQLite Database (*.db)"
        )

        if file_path:
            create_database(file_path, use_age_group_birthday, meet_date)
            self.accept()


def open_meet_setup(parent):
    popup = MeetSetupDialog(parent)
    popup.exec()
