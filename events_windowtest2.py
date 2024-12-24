import sqlite3
from PyQt6.QtWidgets import (
    QVBoxLayout, QTableWidget, QGroupBox, QRadioButton, QHBoxLayout,
    QMainWindow, QPushButton, QHeaderView, QTableWidgetItem, QMessageBox,
    QComboBox, QWidget, QLineEdit, QApplication
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from functools import partial
from resource_path import resource_path

_events_window_instance = None  # Global reference to the EventsWindow instance

class EventsWindow(QMainWindow):
    def __init__(self, db_file_path, parent=None):
        super().__init__(parent)
        self.db_file_path = db_file_path
        self.setWindowTitle("Events")
        self.setGeometry(100, 100, 1200, 600)

        # Set the window icon using your custom logo
        logo_path = resource_path("images/ms.png")
        self.setWindowIcon(QIcon(logo_path))

        # Main Widget and Layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

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
        self.gender_all.setChecked(True)  # Default selection

        filters_layout.addWidget(gender_group)
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        # Connect gender radio buttons to the filter function
        self.gender_all.toggled.connect(self.filter_rows)
        self.gender_male.toggled.connect(self.filter_rows)
        self.gender_female.toggled.connect(self.filter_rows)
        self.gender_mixed.toggled.connect(self.filter_rows)

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Evt #", "Seeding", "Gender", "Division Name",
            "Event Name", "# of Rounds", "Round Names", "Lanes/Pos", "Advancement"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.cellClicked.connect(self.cell_clicked_action)

        main_layout.addWidget(self.table)

        # Buttons Section
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_group.setLayout(buttons_layout)
        main_layout.addWidget(buttons_group)

        self.setCentralWidget(main_widget)

        self.load_events_data()
        self.delete_button.clicked.connect(self.delete_selected_row)

    def filter_rows(self):
        selected_gender = None
        if self.gender_male.isChecked():
            selected_gender = "Male"
        elif self.gender_female.isChecked():
            selected_gender = "Female"
        elif self.gender_mixed.isChecked():
            selected_gender = "Mixed"

        for row in range(self.table.rowCount()):
            gender_item = self.table.item(row, 2)  # Assuming Gender is in the 3rd column
            if selected_gender is None or gender_item.text() == selected_gender:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def cell_clicked_action(self, row, column):
        if column == 7:  # Replace the cell with a QLineEdit
            cell_data = self.table.item(row, column)
            current_value = cell_data.text() if cell_data else ""

            line_edit = QLineEdit(self.table)
            line_edit.setText(current_value)
            self.table.setCellWidget(row, column, line_edit)
            line_edit.setFocus()

            def on_edit_finished():
                new_value = line_edit.text()
                self.table.setItem(row, column, QTableWidgetItem(new_value))
                self.update_database_column7(row, new_value)
                self.table.setCellWidget(row, column, None)

            line_edit.editingFinished.connect(on_edit_finished)

    def update_database_column7(self, row, new_value):
        if not new_value.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter a valid integer.")
            return

        event_id = self.table.item(row, 0).text()
        try:
            with sqlite3.connect(self.db_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE events 
                    SET number_of_lanes = ? 
                    WHERE event_number = ?
                """, (int(new_value), event_id))
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update the database:\n{e}")

    def load_events_data(self):
        try:
            with sqlite3.connect(self.db_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM events")
                rows = cursor.fetchall()
                self.table.setRowCount(len(rows))

                combo_box_rounds = ["Select", "1", "2", "3", "4"]
                advancement_options = ["Select", "Time", "Place Then Time"]
                rounds_mapping = {
                    "1": "Finals Only",
                    "2": "Prelims/Finals",
                    "3": "Prelims/Semi_Finals/Finals",
                    "4": "Prelims/Quarter/Semis/Finals"
                }

                for row_idx, row_data in enumerate(rows):
                    for col_idx, col_data in enumerate(row_data):
                        if col_idx == 5:  # Number of Rounds column
                            combo_box = QComboBox()
                            combo_box.addItems(combo_box_rounds)
                            combo_box.setCurrentText(str(col_data) if col_data else "Select")
                            combo_box.currentIndexChanged.connect(
                                partial(self.update_event_round, row_idx, combo_box, rounds_mapping))
                            self.table.setCellWidget(row_idx, col_idx, combo_box)
                        elif col_idx == 8:  # Advancement column
                            adv_combo_box = QComboBox()
                            adv_combo_box.addItems(advancement_options)
                            adv_combo_box.setCurrentText(str(col_data) if col_data else "Select")
                            adv_combo_box.currentIndexChanged.connect(
                                partial(self.update_advancement, row_idx, adv_combo_box))
                            self.table.setCellWidget(row_idx, col_idx, adv_combo_box)
                        else:
                            self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load events data:\n{e}")

    def update_event_round(self, row_idx, combo_box, rounds_mapping):
        selected_number = combo_box.currentText()
        if selected_number == "Select":
            return
        rnd_names = rounds_mapping[selected_number]
        event_id = self.table.item(row_idx, 0).text()
        try:
            with sqlite3.connect(self.db_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE events 
                    SET number_of_rounds = ?, round_names = ? 
                    WHERE event_number = ?
                """, (selected_number, rnd_names, event_id))
                conn.commit()
                self.load_events_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update event round:\n{e}")

    def update_advancement(self, row_idx, combo_box):
        selected_value = combo_box.currentText()
        if selected_value == "Select":
            return
        event_id = self.table.item(row_idx, 0).text()
        try:
            with sqlite3.connect(self.db_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE events 
                    SET advancement = ? 
                    WHERE event_number = ?
                """, (selected_value, event_id))
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update advancement:\n{e}")

    def delete_selected_row(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Selection Error", "Please select a row to delete.")
            return

        event_number_item = self.table.item(selected_row, 0)
        if not event_number_item:
            QMessageBox.warning(self, "Error", "Failed to get selected row data.")
            return

        event_number = event_number_item.text()
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete Event #{event_number}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with sqlite3.connect(self.db_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE event_number = ?", (event_number,))
                conn.commit()
                self.load_events_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete event:\n{e}")

def show_event_window(db_file_path):
    global _events_window_instance
    if _events_window_instance is None or not _events_window_instance.isVisible():
        _events_window_instance = EventsWindow(db_file_path)
        _events_window_instance.show()
    else:
        _events_window_instance.raise_()
        _events_window_instance.activateWindow()

if __name__ == "__main__":
    import sys

    db_file_path = r"C:\\MeetSystems\\meet1.db"
    app = QApplication(sys.argv)
    window = EventsWindow(db_file_path)
    window.show()
    sys.exit(app.exec())
