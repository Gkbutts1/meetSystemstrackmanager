import sys
import json
import sqlite3
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMessageBox, QApplication, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt



class ImportDivisionsWindow(QDialog):

    def __init__(self, db_file_path, json_file_path, parent=None):
        super().__init__(parent)
        self.db_file_path = db_file_path
        self.json_file_path = json_file_path
        self.setWindowTitle("Import Divisions")
        self.setGeometry(100, 100, 800, 400)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Dropdown to select a template
        template_layout = QHBoxLayout()
        template_label = QLabel("Select Template:")
        self.template_combo = QComboBox()
        self.template_combo.addItem("Select a template")
        try:
            with open(self.json_file_path, 'r') as file:
                self.templates = json.load(file)

                # Initialize variables
                age_group_keys = []
                non_age_group_keys = []

                # Filter keys based on condition
                if self.check_use_age_group_birthday():
                    age_group_keys = [key for key in self.templates.keys() if "ageGroup" in key]
                else:
                    non_age_group_keys = [key for key in self.templates.keys() if "ageGroup" not in key]

                # Populate combobox
                if age_group_keys:
                    print("Templates with 'ageGroup' found.")
                    self.template_combo.addItems(age_group_keys)
                elif non_age_group_keys:
                    print("Templates without 'ageGroup' found.")
                    self.template_combo.addItems(non_age_group_keys)
                else:
                    print("No templates found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load templates: {e}")
            self.templates = {}

        # if self.check_use_age_group_birthday():
        # # Load templates from the JSON file
        # try:
        #     with open(self.json_file_path, 'r') as file:
        #         self.templates = json.load(file)
        #         # Check if any key in self.templates contains the substring "ageGroup"
        #         if any("ageGroup" in key for key in self.templates.keys()):
        #             print("A template with 'ageGroup' found.")
        #             self.template_combo.addItems(self.templates.keys())
        # except Exception as e:
        #     QMessageBox.critical(self, "Error", f"Failed to load templates: {e}")
        #     self.templates = {}

        self.template_combo.currentIndexChanged.connect(self.display_template_data)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)

        # Create the table widget
        self.data_table = QTableWidget()

        if self.check_use_age_group_birthday():
            # Configure the table for age group
            self.data_table.setColumnCount(5)
            self.data_table.setHorizontalHeaderLabels(["Div Num", "Name", "From Age", "To Age", "Type"])
        else:
            # Configure the table for non-age group
            self.data_table.setColumnCount(3)
            self.data_table.setHorizontalHeaderLabels(["Div Num", "Name", "Type"])

        # Common configuration
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.verticalHeader().setVisible(False)

        # Add the table to the layout
        layout.addWidget(self.data_table)



        # Buttons for importing and closing
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_template)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_db(self):
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to the database: {e}")
            raise

    def display_template_data(self):
        selected_template = self.template_combo.currentText()
        if selected_template == "Select a template":
            self.data_table.setRowCount(0)
            return

        divisions = self.templates.get(selected_template, [])
        self.data_table.setRowCount(len(divisions))
        print(divisions)

        for row, division in enumerate(divisions, start=1):  # Start numbering at 1
            # self.data_table.setItem(row - 1, 0, QTableWidgetItem(str(row)))  # Division Number (row)
            self.data_table.setItem(row - 1, 0, QTableWidgetItem(division.get("div_num", "")))
            self.data_table.setItem(row - 1, 1, QTableWidgetItem(division.get("name", "")))
            self.data_table.setItem(row - 1, 2, QTableWidgetItem(division.get("from_age", "")))
            self.data_table.setItem(row - 1, 3, QTableWidgetItem(division.get("to_age", "")))
            self.data_table.setItem(row - 1, 4, QTableWidgetItem(division.get("type", "")))

    def import_template(self):
        selected_template = self.template_combo.currentText()
        if selected_template == "Select a template":
            QMessageBox.warning(self, "Selection Error", "Please select a valid template.")
            return

        divisions = self.templates.get(selected_template, [])
        if not divisions:
            QMessageBox.warning(self, "Template Error", "Selected template contains no data.")
            return

        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # Purge divisions table
            cursor.execute("DELETE FROM divisions_age_group")
            # Purge divisions table
            cursor.execute("DELETE FROM divisions_non_age_groups")

            for division in divisions:
                if division["type"] == "age_group":
                    query = """
                        INSERT INTO divisions_age_group (division_number,division_name, from_age, to_age)
                        VALUES (?, ?, ?, ?)
                    """
                    params = (division["div_num"],division["name"], division.get("from_age"), division.get("to_age"))
                else:
                    query = """
                        INSERT INTO divisions_non_age_groups (division_number,division_name)
                        VALUES (?, ?)
                    """
                    params = (division["div_num"],division["name"],)

                cursor.execute(query, params)

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Template imported successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to import template: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

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


def show_import_window(db_file_path, json_file_path):
    app = QApplication(sys.argv)
    window = ImportDivisionsWindow(db_file_path, json_file_path)
    window.exec()



if __name__ == "__main__":
    # Example usage
    db_path= r"C:/MeetSystems/test.db"
    json_path = "json/divisionsTemplate2.json"
    show_import_window(db_path, json_path)
