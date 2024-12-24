import sqlite3
import json
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QWidget, QGroupBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from resource_path import resource_path


class EventSelector(QMainWindow):
    def __init__(self, json_file_path, db_file_path):
        super().__init__()
        self.setWindowTitle("Event Selector")
        self.setGeometry(100, 100, 600, 400)
        self.json_file_path = json_file_path
        self.db_file_path = db_file_path

        self.state_storage = {}  # Dictionary to store state per division-gender combination

        # Set the window icon
        logo_path = resource_path("images/ms.png")
        self.setWindowIcon(QIcon(logo_path))

        # Main layout
        main_layout = QVBoxLayout()

        # Division and Gender dropdowns
        dropdown_layout = QHBoxLayout()
        self.division_label = QLabel("Division:")
        self.division_dropdown = QComboBox()
        self.populate_division_dropdown()
        self.division_dropdown.currentIndexChanged.connect(self.handle_division_gender_change)

        self.gender_label = QLabel("Gender:")
        self.gender_dropdown = QComboBox()
        self.gender_dropdown.addItems(["Male", "Female","Mixed"])
        self.gender_dropdown.currentIndexChanged.connect(self.handle_division_gender_change)

        dropdown_layout.addWidget(self.division_label)
        dropdown_layout.addWidget(self.division_dropdown)
        dropdown_layout.addSpacing(10)  # Optional spacing between dropdowns
        dropdown_layout.addWidget(self.gender_label)
        dropdown_layout.addWidget(self.gender_dropdown)
        # Align all widgets to the left
        dropdown_layout.addStretch()  # This pushes all elements to the left
        main_layout.addLayout(dropdown_layout)

        # Event categories layout
        self.event_layout = QVBoxLayout()
        self.event_groups = {
            "Run": self.create_event_group("Run", self.load_run_events()),
            "Dash": self.create_event_group("Dash", self.load_dash_events()),
            "Hurdles": self.create_event_group("Hurdles", self.load_hurdle_events()),
            "Jumps": self.create_event_group("Jumps", self.load_jump_events()),
            "Throws": self.create_event_group("Throws", self.load_throw_events()),
            "Multi Events": self.create_event_group("Multi Events", self.load_multi_events()),
            "Relay Events": self.create_event_group("Relay Events", self.load_relay_events())
        }

        for group in self.event_groups.values():
            self.event_layout.addWidget(group)

        main_layout.addLayout(self.event_layout)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_selection)
        main_layout.addWidget(self.save_button)

        # Set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Initialize UI for the default selection
        self.handle_division_gender_change()

    def populate_division_dropdown(self):
        try:
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT division_name FROM divisions_age_group ORDER BY division_number ASC")
            divisions = cursor.fetchall()
            self.division_dropdown.clear()
            for division in divisions:
                self.division_dropdown.addItem(division[0])
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def create_event_group(self, title, events):
        group_box = QGroupBox(title)
        group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QGridLayout()
        for index, event in enumerate(events):
            row = index // 6
            col = index % 6
            checkbox = QCheckBox(event)
            layout.addWidget(checkbox, row, col)
        group_box.setLayout(layout)
        return group_box

    def load_run_events(self):
        return self.load_events_by_type("run")

    def load_dash_events(self):
        return self.load_events_by_type("dash")

    def load_jump_events(self):
        return self.load_events_by_type("jump")

    def load_hurdle_events(self):
        return self.load_events_by_type("hurdles")

    def load_relay_events(self):
        return self.load_events_by_type("relay")

    def load_throw_events(self):
        return self.load_events_by_type("throw")

    def load_multi_events(self):
        return self.load_events_by_type("multi")

    def load_events_by_type(self, event_type):
        try:
            with open(self.json_file_path, 'r') as file:
                events = json.load(file)
                filtered_events = [event['event_name'] for event in events if event['type'] == event_type]
                return sorted(filtered_events)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading or parsing JSON file: {e}")
            return []

    def handle_division_gender_change(self):
        current_division = self.division_dropdown.currentText()
        current_gender = self.gender_dropdown.currentText()
        key = (current_division, current_gender)

        # Save current state
        if hasattr(self, 'previous_key'):
            self.state_storage[self.previous_key] = {
                checkbox.text(): checkbox.isChecked()
                for group in self.event_groups.values()
                for checkbox in group.findChildren(QCheckBox)
            }

        # Clear UI
        for group in self.event_groups.values():
            for checkbox in group.findChildren(QCheckBox):
                checkbox.setChecked(False)

        # Restore state for the new selection
        if key in self.state_storage:
            for group in self.event_groups.values():
                for checkbox in group.findChildren(QCheckBox):
                    checkbox.setChecked(self.state_storage[key].get(checkbox.text(), False))

        self.previous_key = key

    def save_selection(self):
        current_division = self.division_dropdown.currentText()
        current_gender = self.gender_dropdown.currentText()
        key = (current_division, current_gender)

        selected_events = {
            checkbox.text(): checkbox.isChecked()
            for group in self.event_groups.values()
            for checkbox in group.findChildren(QCheckBox)
        }

        self.state_storage[key] = selected_events

        # Persist to database
        self.save_to_database([(event, current_division, current_gender)
                               for event, checked in selected_events.items() if checked])

    def save_to_database(self, events):
        """
        Saves the selected events into the database, ensuring event numbers are sequential.
        Renumbers event numbers after any insert or update operation.
        """
        try:
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()

            # Insert or update events
            for event in events:
                # Check if the event already exists
                cursor.execute("""
                    SELECT event_number FROM events
                    WHERE event_name = ? AND division_name = ? AND gender = ?
                """, (event[0], event[1], event[2]))

                result = cursor.fetchone()

                if result is not None:
                    # Update existing event
                    cursor.execute("""
                        UPDATE events
                        SET gender = ?, division_name = ?, event_name = ?
                        WHERE event_number = ?
                    """, (event[2], event[1], event[0], result[0]))
                else:
                    # Insert new event
                    seeding = "Not Seeded"
                    cursor.execute("""
                        INSERT INTO events (seeding, gender, division_name, event_name)
                        VALUES (?, ?, ?, ?)
                    """, (seeding, event[2], event[1], event[0]))

            # Renumber event numbers sequentially
            self.renumber_event_numbers(cursor)

            conn.commit()
            print("Events saved and renumbered successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    def renumber_event_numbers(self, cursor):
        """
        Renumbers the 'event_number' column sequentially (1, 2, 3, ...) based on row order.
        """
        try:
            # Fetch all rows ordered by ROWID (default insertion order)
            cursor.execute("SELECT ROWID, event_number FROM events ORDER BY ROWID")
            rows = cursor.fetchall()

            # Renumber event numbers
            for index, (rowid, _) in enumerate(rows, start=1):
                cursor.execute("UPDATE events SET event_number = ? WHERE ROWID = ?", (index, rowid))

            print("Event numbers renumbered successfully.")
        except sqlite3.Error as e:
            print(f"Failed to renumber event numbers: {e}")


if __name__ == "__main__":
    json_file_path = "json/events4.json"
    db_file_path = r"C:\MeetSystems\meet1.db"
    app = QApplication([])
    window = EventSelector(json_file_path, db_file_path)
    window.show()
    app.exec()
