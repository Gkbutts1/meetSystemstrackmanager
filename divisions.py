import sys
import sqlite3

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from resource_path import resource_path


class DivisionsWindow(QDialog):
    def __init__(self, db_file_path, parent=None):
        super().__init__(parent)
        self.open_division_templates_btn = None
        self.db_file_path = db_file_path
        self.setWindowTitle("Divisions Table")
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        self.init_ui()

        # Set the window icon using your custom logo from resource_path import resource_path
        logo_path = resource_path("images/ms.png")  # Replace with the actual path to your logo
        self.setWindowIcon(QIcon(logo_path))

        # Load data based on the `use_age_group_birthday` setting
        if self.check_use_age_group_birthday():
            self.load_age_group_divisions_data()
        else:
            self.load_non_age_group_divisions_data()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Table to display divisions data
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # Form layout for adding new rows
        form_layout = QHBoxLayout()

        self.division_number_input = QLineEdit()
        self.division_number_input.setPlaceholderText("Division Number")
        form_layout.addWidget(self.division_number_input)

        self.division_abbr_input = QLineEdit()
        self.division_abbr_input.setPlaceholderText("Division Abbreviation")
        form_layout.addWidget(self.division_abbr_input)

        self.division_name_input = QLineEdit()
        self.division_name_input.setPlaceholderText("Division Name")
        form_layout.addWidget(self.division_name_input)

        if self.check_use_age_group_birthday():
            self.from_age_input = QLineEdit()
            self.from_age_input.setPlaceholderText("From Age")
            form_layout.addWidget(self.from_age_input)

            self.to_age_input = QLineEdit()
            self.to_age_input.setPlaceholderText("To Age")
            form_layout.addWidget(self.to_age_input)

            self.age_as_of_date_input = QLineEdit()
            self.age_as_of_date_input.setPlaceholderText("Age As Of Date (YYYY-MM-DD)")
            form_layout.addWidget(self.age_as_of_date_input)

        self.add_row_btn = QPushButton("Add Row")
        self.add_row_btn.clicked.connect(self.add_row)
        form_layout.addWidget(self.add_row_btn)

        main_layout.addLayout(form_layout)

        # Buttons layout
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self.refresh_btn)

        # Clear All Button
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_data)
        btn_layout.addWidget(self.clear_all_btn)

        # Open divisionTemplates.py button
        self.open_division_templates_btn = QPushButton("Open Division Templates")
        self.open_division_templates_btn.clicked.connect(self.open_division_templates)
        btn_layout.addWidget(self.open_division_templates_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def connect_db(self):
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to the database: {e}")
            raise

    def check_use_age_group_birthday(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT setting_value 
                FROM settings 
                WHERE setting_name = 'use_age_group_birthday'
            """)
            result = cursor.fetchone()
            conn.close()
            return result and result[0].lower() == 'true'
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to check settings: {e}")
            return False

    def load_age_group_divisions_data(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT division_number, division_abbr, division_name, from_age, to_age, age_as_of_date 
                FROM divisions_age_group 
                ORDER BY division_number ASC
            """) # Purge divisions table


            self.populate_table(cursor.fetchall(), ["Division Number", "Division Abbr", "Division Name", "From Age", "To Age", "Age As Of Date"])
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch age group divisions data: {e}")

    def load_non_age_group_divisions_data(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()



            cursor.execute("""
                SELECT division_number, division_abbr, division_name
                FROM divisions_non_age_groups 
                ORDER BY division_number ASC
            """)
            self.populate_table(cursor.fetchall(), ["Division Number", "Division Abbr", "Division Name"])
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch non-age group divisions data: {e}")

    def populate_table(self, data, headers):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col, item)
        self.table.blockSignals(False)
        self.table.itemChanged.connect(self.handle_item_changed)

    def handle_item_changed(self, item):
        if item.column() == 0:
            return

        row = item.row()
        col = item.column()
        new_value = item.text()
        division_id = self.table.item(row, 0).text()

        if self.check_use_age_group_birthday():
            table_name = "divisions_age_group"
            columns = ["division_number", "division_abbr", "division_name", "from_age", "to_age", "age_as_of_date"]
        else:
            table_name = "divisions_non_age_groups"
            columns = ["division_number", "division_abbr", "division_name"]

        column_name = columns[col - 1]

        query = f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?"
        params = (new_value, division_id)

        try:
            self.table.blockSignals(True)
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Value updated successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update value: {e}")
            self.refresh_data()
        finally:
            self.table.blockSignals(False)

    def add_row(self):
        division_number = self.division_number_input.text()
        division_abbr = self.division_abbr_input.text()
        division_name = self.division_name_input.text()

        if self.check_use_age_group_birthday():
            from_age = self.from_age_input.text()
            to_age = self.to_age_input.text()
            age_as_of_date = self.age_as_of_date_input.text()

            if not all([division_number, division_abbr, division_name, from_age, to_age]):
                QMessageBox.warning(self, "Input Error", "Please fill in all fields for age group divisions.")
                return

            query = """
                INSERT INTO divisions_age_group (division_number, division_abbr, division_name, from_age, to_age, age_as_of_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (division_number, division_abbr, division_name, from_age, to_age, age_as_of_date)
        else:
            if not all([division_number, division_abbr, division_name]):
                QMessageBox.warning(self, "Input Error", "Please fill in all required fields.")
                return

            query = """
                INSERT INTO divisions_non_age_groups (division_number, division_abbr, division_name)
                VALUES (?, ?, ?)
            """
            params = (division_number, division_abbr, division_name)

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            self.refresh_data()
            QMessageBox.information(self, "Success", "Row added successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add row: {e}")

    def refresh_data(self):
        self.table.blockSignals(True)
        if self.check_use_age_group_birthday():
            self.load_age_group_divisions_data()
        else:
            self.load_non_age_group_divisions_data()
        self.table.blockSignals(False)

    def clear_all_data(self):
        """Clears all data from the relevant database table and refreshes the UI."""
        if self.check_use_age_group_birthday():
            table_name = "divisions_age_group"
        else:
            table_name = "divisions_non_age_groups"

        confirm = QMessageBox.question(
            self,
            "Confirm Clear All",
            "Are you sure you want to clear all data? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {table_name}")
                conn.commit()
                conn.close()
                self.refresh_data()
                QMessageBox.information(self, "Success", "All data cleared successfully.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to clear data: {e}")

    def open_division_templates(self):
        json_path = "json/divisionsTemplate.json"
        from divisionTemplates import ImportDivisionsWindow
        try:
            window = ImportDivisionsWindow(self.db_file_path, json_path)
            window.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open divisionTemplates window: {e}")


def show_divisions_window(db_file_path):
    divisions_window = DivisionsWindow(db_file_path)
    divisions_window.exec()
