import sys
import sqlite3
from PyQt6.QtGui import QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QCalendarWidget, QGridLayout, QApplication,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime

from bib_assigner import assign_bib_numbers
from PyQt6.QtWidgets import QSpacerItem, QSizePolicy
# Global variables
global_db_file_path = None
global_age_group_birthday = False


class AthletesWindow(QDialog):
    def __init__(self, db_file_path, global_age_group_birthday, parent=None):
        super().__init__(parent)
        self.db_file_path = db_file_path
        self.global_age_group_birthday = global_age_group_birthday
        self.setWindowTitle("Athletes Table")
        self.setGeometry(100, 100, 1200, 600)
        logo_path = "images/ms.png"  # Replace with the actual path to your logo
        self.setWindowIcon(QIcon(logo_path))
        self.use_age_group_birthday = self.get_age_group_birthday_setting()
        self.sort_by_column = "Bib Number"  # Default sorting column

        # Set the window flags to enable minimize and maximize buttons
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint
        )

        self.selected_team = "All Teams"  # Initial value to load all athletes
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Team Selection Dropdown
        team_selection_layout = QHBoxLayout()

        # Add a spacer item to push the label to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        team_selection_layout.addItem(spacer)

        team_selection_label = QLabel("Select Team:")

        team_selection_layout.addWidget(team_selection_label)

        self.team_selection_combo = QComboBox()
        self.team_selection_combo.addItem("All Teams")
        self.load_teams_data()  # Load teams into the combo box
        self.team_selection_combo.currentIndexChanged.connect(self.update_team_selection)


        team_selection_layout.addWidget(self.team_selection_combo)
        main_layout.addLayout(team_selection_layout)

        # Athlete Count Label
        self.athlete_count_label = QLabel("Athlete Count: 0", self)
        main_layout.addWidget(self.athlete_count_label)

        # Table to display athletes data
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Bib Number", "Last Name", "First Name", "MI", "Gender", "DOB", "Age", "Team ID",
            "Team Name", "Membership Number"
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.cellClicked.connect(self.select_athlete)
        main_layout.addWidget(self.table)

        # Sorting Buttons Layout
        sorting_layout = QHBoxLayout()
        self.bib_sort_btn = QPushButton("Sort by Bib Number")
        self.bib_sort_btn.clicked.connect(lambda: self.set_sorting_column("Bib Number"))
        self.last_name_sort_btn = QPushButton("Sort by Last Name")
        self.last_name_sort_btn.clicked.connect(lambda: self.set_sorting_column("Last Name"))
        self.first_name_sort_btn = QPushButton("Sort by First Name")
        self.first_name_sort_btn.clicked.connect(lambda: self.set_sorting_column("First Name"))
        self.team_sort_btn = QPushButton("Sort by Team Name")
        self.team_sort_btn.clicked.connect(lambda: self.set_sorting_column("Team Name"))

        sorting_layout.addWidget(self.bib_sort_btn)
        sorting_layout.addWidget(self.last_name_sort_btn)
        sorting_layout.addWidget(self.first_name_sort_btn)
        sorting_layout.addWidget(self.team_sort_btn)
        main_layout.addLayout(sorting_layout)

        # Form Layout for input fields
        form_layout = QGridLayout()

        # Row 1: Last Name, First Name, MI
        form_layout.addWidget(QLabel("Last Name:"), 0, 0)
        self.entry_last_name = QLineEdit()
        form_layout.addWidget(self.entry_last_name, 0, 1)

        form_layout.addWidget(QLabel("First Name:"), 0, 2)
        self.entry_first_name = QLineEdit()
        form_layout.addWidget(self.entry_first_name, 0, 3)

        form_layout.addWidget(QLabel("MI:"), 0, 4)
        self.entry_mi = QLineEdit()
        form_layout.addWidget(self.entry_mi, 0, 5)

        # Row 2: Gender (Dropdown), DOB (with calendar button)
        form_layout.addWidget(QLabel("Gender:"), 1, 0)
        self.entry_gender = QComboBox()
        self.entry_gender.addItems(["M", "F"])
        form_layout.addWidget(self.entry_gender, 1, 1)

        form_layout.addWidget(QLabel("DOB:"), 1, 2)
        self.entry_dob = QLineEdit()
        self.entry_dob.setReadOnly(True)
        form_layout.addWidget(self.entry_dob, 1, 3)

        if self.global_age_group_birthday:
            self.dob_calendar_btn = QPushButton("Select DOB")
            self.dob_calendar_btn.clicked.connect(self.open_calendar_popup)
            form_layout.addWidget(self.dob_calendar_btn, 1, 4)

        # Row 3: Team (ComboBox)
        form_layout.addWidget(QLabel("Team:"), 2, 0)
        self.team_combo = QComboBox()
        self.load_teams_data_for_inputs()  # Load teams into the combo box
        form_layout.addWidget(self.team_combo, 2, 1, 1, 3)

        # Row 4: Bib Number, Membership Number
        form_layout.addWidget(QLabel("Bib Number:"), 3, 0)
        self.entry_bib_number = QLineEdit()
        self.entry_bib_number.setValidator(QIntValidator())  # Only allow integers in Bib Number field
        form_layout.addWidget(self.entry_bib_number, 3, 1)

        form_layout.addWidget(QLabel("Membership Number:"), 3, 2)
        self.entry_membership_number = QLineEdit()
        form_layout.addWidget(self.entry_membership_number, 3, 3)

        main_layout.addLayout(form_layout)

        # Add buttons for actions
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Athlete")
        self.add_btn.clicked.connect(self.add_athlete)

        self.update_btn = QPushButton("Update Athlete")
        self.update_btn.clicked.connect(self.update_athlete)

        self.delete_btn = QPushButton("Delete Athlete")
        self.delete_btn.clicked.connect(self.delete_athlete)

        self.clear_btn = QPushButton("Clear Fields")
        self.clear_btn.clicked.connect(self.clear_inputs)

        self.assign_bib_btn = QPushButton("Assign Bib Numbers")
        self.assign_bib_btn.clicked.connect(lambda: assign_bib_numbers(self))

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.assign_bib_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Load athletes data
        self.load_athletes_data()

    def update_team_selection(self):
        """ Update the selected team filter and reload athlete data. """
        self.selected_team = self.team_selection_combo.currentText()
        self.load_athletes_data()

    def load_athletes_data(self):
        """ Load athlete data from the database into the table, filtered by the selected team and sorted by the specified column. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            if self.selected_team == "All Teams":
                cursor.execute("""
                    SELECT bib_number, last_name, first_name, middle_initials, gender, dob, age, 
                    team_code, team_name, membership_number
                    FROM athletes
                """)
            else:
                cursor.execute("""
                    SELECT bib_number, last_name, first_name, middle_initials, gender, dob, age, 
                    team_code, team_name, membership_number
                    FROM athletes
                    WHERE team_name = ?
                """, (self.selected_team,))

            athletes_data = cursor.fetchall()

            # Get the meet year from the settings
            meet_year = self.get_meet_year()

            # Update the athlete count label
            self.athlete_count_label.setText(f"Athlete Count: {len(athletes_data)}")

            # Sort the data based on the selected column
            column_mapping = {
                "Bib Number": 0,
                "Last Name": 1,
                "First Name": 2,
                "Team Name": 8  # Adjusted to match the index in athletes_data
            }
            col_index = column_mapping.get(self.sort_by_column, 0)

            # Apply sorting as integer if sorting by "Bib Number"
            if self.sort_by_column == "Bib Number":
                sorted_data = sorted(athletes_data, key=lambda x: self.safe_cast(x[col_index], int, 0))
            else:
                sorted_data = sorted(athletes_data, key=lambda x: self.safe_cast(x[col_index], str))

            self.table.setRowCount(0)  # Clear all rows before reloading

            # Iterate over each athlete's data and display it
            for row_data in sorted_data:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # Parse DOB and calculate age if needed
                dob = row_data[5]  # `dob` is at index 5
                if dob and meet_year:
                    try:
                        dob_date = datetime.strptime(dob, '%m/%d/%Y') if isinstance(dob, str) else dob
                        age = self.calculate_age_as_of_december_31(dob_date, meet_year)
                    except ValueError:
                        age = None
                else:
                    age = None

                # Construct display_data to match the table columns
                display_data = [
                    row_data[0],  # Bib Number
                    row_data[1],  # Last Name
                    row_data[2],  # First Name
                    row_data[3],  # Middle Initials
                    row_data[4],  # Gender
                    row_data[5],  # DOB
                    age,  # Calculated Age
                    row_data[7],  # Team ID
                    row_data[8],  # Team Name
                    row_data[9]  # Membership Number
                ]
                for col, data in enumerate(display_data):
                    item = QTableWidgetItem(str(data) if data is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make cells non-editable
                    self.table.setItem(row, col, item)

            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch athletes data: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def load_teams_data(self):
        """ Load team data from the database into the team combo box for filtering. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT team_name FROM teams ORDER BY team_name ASC")
            teams = cursor.fetchall()
            for team in teams:
                self.team_selection_combo.addItem(team[0])
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load teams data: {e}")

    def load_teams_data_for_inputs(self):
        """ Load team data into the team combo box for form inputs. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT team_name, team_code FROM teams ORDER BY team_name ASC")
            teams = cursor.fetchall()
            self.team_combo.clear()
            for team in teams:
                team_code, team_name = team
                self.team_combo.addItem(f"{team_code}", team_name)

            unattached_index = self.team_combo.findText("Unattached", Qt.MatchFlag.MatchContains)
            if unattached_index != -1:
                self.team_combo.setCurrentIndex(unattached_index)

            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load teams data: {e}")

    def open_calendar_popup(self):
        """ Open a calendar widget to select DOB. """
        self.calendar_dialog = QDialog(self)
        self.calendar_dialog.setWindowTitle("Select Date")
        self.calendar_dialog.setGeometry(300, 200, 400, 400)

        layout = QVBoxLayout(self.calendar_dialog)

        # Year and Month selectors
        year_selector_layout = QHBoxLayout()
        self.year_selector = QComboBox()
        self.year_selector.addItems([str(year) for year in range(1900, 2101)])
        self.year_selector.setCurrentText(str(QDate.currentDate().year()))

        self.month_selector = QComboBox()
        self.month_selector.addItems([str(month) for month in range(1, 13)])
        self.month_selector.setCurrentText(str(QDate.currentDate().month()))

        year_selector_layout.addWidget(QLabel("Year:"))
        year_selector_layout.addWidget(self.year_selector)
        year_selector_layout.addWidget(QLabel("Month:"))
        year_selector_layout.addWidget(self.month_selector)

        self.year_selector.currentIndexChanged.connect(self.update_calendar)
        self.month_selector.currentIndexChanged.connect(self.update_calendar)

        layout.addLayout(year_selector_layout)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        btn_select = QPushButton("Select")
        btn_select.clicked.connect(self.select_date)
        layout.addWidget(btn_select)

        self.calendar_dialog.exec()

    def update_calendar(self):
        """ Update calendar when year or month changes. """
        year = int(self.year_selector.currentText())
        month = int(self.month_selector.currentText())
        day = min(self.calendar.selectedDate().day(), QDate(year, month, 1).daysInMonth())
        self.calendar.setSelectedDate(QDate(year, month, day))

    def select_date(self):
        """ Set the selected date from the calendar. """
        selected_date = self.calendar.selectedDate().toString("MM/dd/yyyy")
        self.entry_dob.setText(selected_date)
        self.calendar_dialog.close()

    def connect_db(self):
        """ Connect to the SQLite database. """
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to the database: {e}")
            sys.exit(1)

    def set_sorting_column(self, column_name):
        """ Set the column by which the athletes data should be sorted. """
        self.sort_by_column = column_name
        self.load_athletes_data()

    def get_meet_year(self):
        """Fetch the meet year from the settings table."""
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT setting_meet_date FROM settings WHERE setting_name = 'use_age_group_birthday'")
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                meet_year = datetime.strptime(result[0], "%m/%d/%Y").year
                return meet_year
            else:
                return None

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch meet year: {e}")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error occurred: {e}")
            return None

    def calculate_age_as_of_december_31(self, dob, meet_year):
        try:
            # Ensure `dob` is a datetime object
            if isinstance(dob, str):
                dob = datetime.strptime(dob, '%m/%d/%Y')  # Adjust format as needed
            december_31 = datetime(meet_year, 12, 31)
            age = december_31.year - dob.year - ((december_31.month, december_31.day) < (dob.month, dob.day))
            return age
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Date parsing error for DOB: {dob}. {e}")
            return None

    def safe_cast(self, value, to_type, default=None):
        """Safely cast a value to a given type."""
        try:
            return to_type(value)
        except (ValueError, TypeError):
            return default if default is not None else value

    def add_athlete(self):
        """ Add a new athlete to the database. """
        if not self.validate_inputs():
            return

        # Check for unique bib number
        if self.check_if_bib_exists(self.entry_bib_number.text()):
            QMessageBox.warning(self, "Duplicate Bib Number", "Bib Number must be unique.")
            return

        # Calculate age based on dob and current meet year
        dob = self.entry_dob.text()
        meet_year = self.get_meet_year()
        age = self.calculate_age_as_of_december_31(dob, meet_year) if dob and meet_year else None

        # Debug: Print the age to ensure it is being calculated correctly
        print(f"Calculated age for manual entry: {age}")

        athlete_data = (
            self.entry_last_name.text(), self.entry_first_name.text(), self.entry_mi.text(),
            self.entry_gender.currentText(), dob, age,  # Include the calculated age
            self.team_combo.currentData(), self.team_combo.currentText(),
            self.entry_bib_number.text(), self.entry_membership_number.text()
        )

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO athletes 
                (last_name, first_name, middle_initials, gender, dob, age, 
                team_code, team_name, bib_number, membership_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, athlete_data)
            conn.commit()
            conn.close()

            self.clear_inputs()
            self.load_athletes_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add athlete: {e}")

    def check_if_athlete_exists(self, last_name, first_name, dob):
        """ Check if an athlete with the same last name, first name, and dob exists. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM athletes
                WHERE last_name = ? AND first_name = ? AND dob = ?
            """, (last_name, first_name, dob))
            result = cursor.fetchone()
            conn.close()
            return result[0] > 0
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to check athlete: {e}")
            return False

    def check_if_bib_exists(self, bib_number):
        """ Check if a bib number is unique in the database. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM athletes WHERE bib_number = ?", (bib_number,))
            result = cursor.fetchone()
            conn.close()
            return result[0] > 0  # Returns True if bib number exists
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to check bib number: {e}")
            return False

    def get_age_group_birthday_setting(self):
        """ Fetch the 'use_age_group_birthday' setting from the settings table. """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT setting_value FROM settings WHERE setting_name = 'use_age_group_birthday'
            """)
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'True'
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch settings: {e}")
            return False

    def update_athlete(self):
        """ Update the selected athlete's information. """
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an athlete to update.")
            return

        if not self.validate_inputs():
            return

        updated_athlete_data = (
            self.entry_last_name.text(),
            self.entry_first_name.text(),
            self.entry_mi.text(),
            self.entry_gender.currentText(),
            self.entry_dob.text(),
            self.team_combo.currentData(),
            self.team_combo.currentText(),
            self.entry_bib_number.text(),
            self.entry_membership_number.text(),
            selected_items[0].text()
        )

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE athletes SET 
                    last_name = ?, first_name = ?, middle_initials = ?, gender = ?, 
                    dob = ?, team_code = ?, team_name = ?, bib_number = ?, membership_number = ? 
                WHERE bib_number = ?
            """, updated_athlete_data)
            conn.commit()
            conn.close()
            self.load_athletes_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update athlete: {e}")

    def delete_athlete(self):
        """ Delete the selected athlete from the database. """
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an athlete to delete.")
            return

        athlete_last_name = selected_items[1].text()

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM athletes WHERE last_name = ?", (athlete_last_name,))
            conn.commit()
            conn.close()

            self.load_athletes_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete athlete: {e}")

    def validate_inputs(self):
        """ Validate the inputs before adding/updating an athlete. """
        if not self.entry_last_name.text() or not self.entry_first_name.text():
            QMessageBox.warning(self, "Input Error", "Last Name and First Name are required.")
            return False

        if self.use_age_group_birthday and not self.entry_dob.text():
            QMessageBox.warning(self, "Input Error", "DOB is required as per settings.")
            return False

        return True

    def clear_inputs(self):
        """ Clear all input fields. """
        self.entry_last_name.clear()
        self.entry_first_name.clear()
        self.entry_mi.clear()
        self.entry_gender.setCurrentIndex(0)
        self.entry_dob.clear()
        self.team_combo.setCurrentIndex(self.team_combo.findText("Unattached", Qt.MatchFlag.MatchContains))
        self.entry_bib_number.clear()
        self.entry_membership_number.clear()

    def select_athlete(self):
        """ Populate the input fields with the selected athlete's data. """
        selected_items = self.table.selectedItems()
        if selected_items:
            self.entry_bib_number.setText(selected_items[0].text())
            self.entry_last_name.setText(selected_items[1].text())
            self.entry_first_name.setText(selected_items[2].text())
            self.entry_mi.setText(selected_items[3].text())

            gender_index = self.entry_gender.findText(selected_items[4].text())
            if gender_index != -1:
                self.entry_gender.setCurrentIndex(gender_index)

            self.entry_dob.setText(selected_items[5].text())
            team_code = selected_items[6].text()
            index = self.team_combo.findData(team_code)
            if index != -1:
                self.team_combo.setCurrentIndex(index)

            self.entry_membership_number.setText(selected_items[8].text())

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     db_path = "your_database_path.db"  # Replace with your actual database path
#     athletes_window = AthletesWindow(db_path, global_age_group_birthday)
#     athletes_window.exec()
#     sys.exit(app.exec())
