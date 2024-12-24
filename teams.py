import sys
import sqlite3

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from resource_path import resource_path

class TeamsWindow(QDialog):
    def __init__(self, db_file_path, parent=None):
        super().__init__(parent)
        self.db_file_path = db_file_path
        self.setWindowTitle("Teams Table")
        self.setGeometry(100, 100, 800, 400)
        # Set the window icon using your custom logo from resource_path import resource_path
        logo_path = resource_path("images/ms.png")  # Replace with the actual path to your logo
        self.setWindowIcon(QIcon(logo_path))

        # Set the window flags to enable minimize and maximize buttons
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        self.init_ui()

        print(db_file_path)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Table to display teams data
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Team Name", "Team Code"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.cellClicked.connect(self.select_team)
        main_layout.addWidget(self.table)

        # Form Layout for input fields
        form_layout = QVBoxLayout()

        # Team Name
        form_layout.addWidget(QLabel("Team Name:"))
        self.entry_team_name = QLineEdit()
        form_layout.addWidget(self.entry_team_name)

        # Team Code
        form_layout.addWidget(QLabel("Team Code:"))
        self.entry_team_code = QLineEdit()
        form_layout.addWidget(self.entry_team_code)

        # Add buttons for actions (Add, Update, Delete, Clear)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Team")
        self.add_btn.clicked.connect(self.add_team)
        self.update_btn = QPushButton("Update Team")
        self.update_btn.clicked.connect(self.update_team)
        self.delete_btn = QPushButton("Delete Team")
        self.delete_btn.clicked.connect(self.delete_team)
        self.clear_btn = QPushButton("Clear Fields")
        self.clear_btn.clicked.connect(self.clear_inputs)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Load teams data
        self.load_teams_data()

    def connect_db(self):
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to the database: {e}")
            sys.exit(1)

    def load_teams_data(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, team_name, team_code FROM teams ORDER BY team_name ASC")
            teams_data = cursor.fetchall()

            self.table.setRowCount(0)
            for row_data in teams_data:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, data in enumerate(row_data):
                    self.table.setItem(row, col, QTableWidgetItem(str(data)))

            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch teams data: {e}")

    def add_team(self):
        team_name = self.entry_team_name.text()
        team_code = self.entry_team_code.text()

        if not team_name or not team_code:
            QMessageBox.warning(self, "Input Error", "Team Name and Team Code are required.")
            return

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO teams (team_name, team_code) VALUES (?, ?)", (team_name, team_code))
            conn.commit()
            conn.close()

            self.clear_inputs()
            self.load_teams_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add team: {e}")

    def update_team(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a team to update.")
            return

        team_id = selected_items[0].text()
        team_name = self.entry_team_name.text()
        team_code = self.entry_team_code.text()

        # Prevent modifying the "Unattached" team or team with id=1
        if team_id == "1" or team_name.lower() == "unattached":
            QMessageBox.warning(self, "Permission Denied", "You cannot modify the 'Unattached' team or team with ID 1.")
            return

        if not team_name or not team_code:
            QMessageBox.warning(self, "Input Error", "Team Name and Team Code are required.")
            return

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE teams SET team_name = ?, team_code = ? WHERE id = ?", (team_name, team_code, team_id))
            conn.commit()
            conn.close()

            self.load_teams_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update team: {e}")

    def delete_team(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a team to delete.")
            return

        team_id = selected_items[0].text()
        team_name = selected_items[1].text()
        team_code = selected_items[2].text()

        # Prevent deleting the "Unattached" team or team with id=1
        if team_id == "1" or team_name.lower() == "unattached":
            QMessageBox.warning(self, "Permission Denied", "You cannot delete the 'Unattached' team or team with ID 1.")
            return

        # Show a confirmation warning
        confirm_msg = QMessageBox()
        confirm_msg.setIcon(QMessageBox.Icon.Warning)
        confirm_msg.setWindowTitle("Confirm Deletion")
        confirm_msg.setText(f"Deleting the team '{team_name}' will also delete all associated athletes. Are you sure?")
        confirm_msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_msg.setDefaultButton(QMessageBox.StandardButton.No)
        response = confirm_msg.exec()

        if response == QMessageBox.StandardButton.Yes:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()

                # Delete athletes associated with the team
                cursor.execute("DELETE FROM athletes WHERE team_code = ?", (team_code,))

                # Delete the team itself
                cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success",
                                        f"Team '{team_name}' and all associated athletes have been deleted.")
                self.load_teams_data()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete team and associated athletes: {e}")

    def clear_inputs(self):
        self.entry_team_name.clear()
        self.entry_team_code.clear()

    def select_team(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            self.entry_team_name.setText(selected_items[1].text())
            self.entry_team_code.setText(selected_items[2].text())

def show_teams_window(db_file_path):
    teams_window = TeamsWindow(db_file_path)
    teams_window.exec()  # Shows the TeamsWindow as a modal dialog without closing the main application
