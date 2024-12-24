import sqlite3
from PyQt6.QtWidgets import (
    QApplication,QVBoxLayout, QTableWidget, QGroupBox, QRadioButton, QHBoxLayout,
    QPushButton, QHeaderView, QTableWidgetItem, QMessageBox, QDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from resource_path import resource_path

_events_window_instance = None  # Global reference to the EventsWindow instance


class EventsWindow(QDialog):
    def __init__(self, db_file_path, parent=None):
        super().__init__(parent)
        self.db_file_path = db_file_path
        self.setWindowTitle("Events")
        self.setGeometry(100, 100, 1200, 600)

        # Set the window icon using your custom logo
        logo_path = resource_path("images/ms.png")
        self.setWindowIcon(QIcon(logo_path))

        # Main Layout
        main_layout = QVBoxLayout()

        # Filters Section
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout()

        # Gender Filter
        gender_group = QGroupBox("Gender")
        gender_layout = QVBoxLayout()
        self.gender_all = QRadioButton("All")
        self.gender_male = QRadioButton("Male")
        self.gender_female = QRadioButton("Female")
        self.gender_mixed = QRadioButton("Mixed")
        gender_layout.addWidget(self.gender_all)
        gender_layout.addWidget(self.gender_male)
        gender_layout.addWidget(self.gender_female)
        gender_layout.addWidget(self.gender_mixed)
        gender_group.setLayout(gender_layout)

        # Add filters to layout
        filters_layout.addWidget(gender_group)
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Evt #", "Division Name", "Gender",
            "Event Name", "Division", "Rnd", "Finals", "Lanes/Pos"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        main_layout.addWidget(self.table)

        # Buttons Section
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_group.setLayout(buttons_layout)
        main_layout.addWidget(buttons_group)

        # Set Main Layout
        self.setLayout(main_layout)

        # Load data from the database
        self.load_events_data()

        # Connect signals
        self.delete_button.clicked.connect(self.delete_selected_row)

    def load_events_data(self):
        try:
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT event_number, division_name, gender, event_name, event_type, event_rounds, event_lanes_position FROM events")

            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load events data:\n{e}")

    def delete_selected_row(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Selection Error", "Please select a row to delete.")
            return

        # Get the event number of the selected row
        event_number_item = self.table.item(selected_row, 0)
        if event_number_item is None:
            QMessageBox.warning(self, "Error", "Failed to get selected row data.")
            return

        event_number = event_number_item.text()

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete Event #{event_number}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete the row from the database
        try:
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE event_number = ?", (event_number,))
            conn.commit()
            conn.close()

            # Remove the row from the table
            self.table.removeRow(selected_row)

            QMessageBox.information(self, "Success", "Event deleted successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete event:\n{e}")

# def show_event_window(db_file_path):
#     """Launch the EventsWindow and retain the instance to avoid garbage collection."""
#     global _events_window_instance
#     if _events_window_instance is None or not _events_window_instance.isVisible():
#         _events_window_instance = EventsWindow(db_file_path)
#         _events_window_instance.show()
#     else:
#         _events_window_instance.raise_()
#         _events_window_instance.activateWindow()

# if __name__ == "__main__":
#     json_file_path = "json/events4.json"
#     db_file_path = r"C:\MeetSystems\testmeet.db"
#     app = QApplication([])
#     window = show_event_window(json_file_path, db_file_path)
#     window.show()
#     app.exec()

def show_event_window(db_file_path):
    """Launch the EventsWindow."""
    window = EventsWindow(db_file_path)
    window.show()
    return window


if __name__ == "__main__":
    import sys

    db_file_path = r"C:\MeetSystems\testmeet.db"
    app = QApplication(sys.argv)
    window = show_event_window(db_file_path)
    sys.exit(app.exec())