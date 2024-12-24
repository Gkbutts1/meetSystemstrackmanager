from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QDialogButtonBox, QCheckBox
)
from PyQt6.QtGui import QIntValidator
import sqlite3


class BibAssignerDialog(QDialog):
    """Custom dialog to handle team selection, starting and ending bib numbers in one popup."""

    def __init__(self, window):
        super().__init__(window)
        self.setWindowTitle("Assign Bib Numbers")
        self.layout = QVBoxLayout(self)

        self.window = window

        # Add a label for the athlete count
        self.athlete_count_label = QLabel("Athlete Count: 0", self)
        self.layout.addWidget(self.athlete_count_label)

        # Create a combobox for selecting team
        self.team_combobox = QComboBox(self)
        self.team_combobox.addItem("All Teams")

        # Fetch all teams from the database and add them to the combobox
        conn = self.window.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT team_name FROM teams")
        teams = cursor.fetchall()
        for team in teams:
            self.team_combobox.addItem(team[0])
        conn.close()

        # Connect the combobox selection to update the athlete count
        self.team_combobox.currentIndexChanged.connect(self.update_athlete_count)

        # Create QLineEdits for inputting start and end bib numbers (manual input without arrows)
        self.start_bib_label = QLabel("Enter Starting Bib Number:", self)
        self.start_bib_input = QLineEdit(self)
        self.start_bib_input.setValidator(QIntValidator(1, 99999))  # Only allow integers, adjust range as needed

        self.end_bib_label = QLabel("Enter Ending Bib Number:", self)
        self.end_bib_input = QLineEdit(self)
        self.end_bib_input.setValidator(QIntValidator(1, 99999))  # Only allow integers, adjust range as needed

        # Add checkbox to make ending bib optional
        self.assign_all_checkbox = QCheckBox("Assign bib numbers to all athletes (ignore ending bib)", self)
        self.assign_all_checkbox.stateChanged.connect(self.toggle_end_bib)

        # Add widgets to layout
        self.layout.addWidget(QLabel("Choose a team or 'All Teams':", self))
        self.layout.addWidget(self.team_combobox)
        self.layout.addWidget(self.start_bib_label)
        self.layout.addWidget(self.start_bib_input)
        self.layout.addWidget(self.end_bib_label)
        self.layout.addWidget(self.end_bib_input)
        self.layout.addWidget(self.assign_all_checkbox)

        # Create buttons for OK and Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

        # Set dialog layout
        self.setLayout(self.layout)

        # Update the athlete count when the dialog is initialized
        self.update_athlete_count()

    def toggle_end_bib(self, state):
        """Enable or disable the ending bib number based on the checkbox state."""
        self.end_bib_input.setEnabled(state == 0)  # Disable if checkbox is checked

    def get_inputs(self):
        """Return the selected team, start bib number, and optionally the end bib number."""
        start_bib = int(self.start_bib_input.text()) if self.start_bib_input.text() else None
        end_bib = int(
            self.end_bib_input.text()) if self.end_bib_input.isEnabled() and self.end_bib_input.text() else None
        return (self.team_combobox.currentText(), start_bib, end_bib)

    def update_athlete_count(self):
        """Update the athlete count based on the selected team."""
        selected_team = self.team_combobox.currentText()
        conn = self.window.connect_db()
        cursor = conn.cursor()

        # Fetch the number of athletes based on the selected team
        if selected_team == "All Teams":
            cursor.execute("SELECT COUNT(*) FROM athletes")
        else:
            cursor.execute("SELECT COUNT(*) FROM athletes WHERE team_name = ?", (selected_team,))

        athlete_count = cursor.fetchone()[0]
        conn.close()

        # Update the athlete count label
        self.athlete_count_label.setText(f"Athlete Count: {athlete_count}")


def assign_bib_numbers(window):
    """Assign bib numbers to athletes using a custom dialog with all inputs in one window."""
    try:
        # Show the custom BibAssignerDialog to get inputs
        dialog = BibAssignerDialog(window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            team_selection, start_bib, end_bib = dialog.get_inputs()

            # Validate that starting bib is provided
            if start_bib is None:
                QMessageBox.warning(window, "Input Error", "Starting bib number is required.")
                return

            # Validate that the starting bib number is less than or equal to the ending bib number
            if end_bib is not None and start_bib > end_bib:
                QMessageBox.warning(window, "Input Error",
                                    "The starting bib number cannot be greater than the ending bib number.")
                return

            # Connect to the database
            conn = window.connect_db()
            cursor = conn.cursor()

            # Build the query based on team selection and ensure athletes are sorted by team name and last name
            if team_selection == "All Teams":
                cursor.execute("""
                    SELECT id, last_name, first_name, team_name, bib_number 
                    FROM athletes 
                    ORDER BY team_name ASC, last_name ASC
                """)
            else:
                cursor.execute("""
                    SELECT id, last_name, first_name, team_name, bib_number
                    FROM athletes 
                    WHERE team_name = ? 
                    ORDER BY last_name ASC
                """, (team_selection,))

            athletes = cursor.fetchall()

            # Check if there are athletes to assign bib numbers to
            if not athletes:
                QMessageBox.warning(window, "No Athletes", "No athletes found for the selected team.")
                conn.close()
                return

            # Assign bib numbers sequentially as integers
            bib_number = start_bib
            for athlete in athletes:
                if end_bib is not None and bib_number > end_bib:
                    break
                athlete_id = athlete[0]
                cursor.execute("""
                    UPDATE athletes 
                    SET bib_number = ? 
                    WHERE id = ?
                """, (bib_number, athlete_id))
                bib_number += 1

            conn.commit()
            conn.close()

            # Reload athletes data to reflect changes
            window.load_athletes_data()
            QMessageBox.information(window, "Success", "Bib numbers assigned successfully.")

    except sqlite3.Error as e:
        QMessageBox.critical(window, "Database Error", f"Failed to assign bib numbers: {e}")
    except Exception as e:
        QMessageBox.critical(window, "Error", f"An unexpected error occurred: {e}")
