import sys
import os
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon, QAction
from PyQt6.QtCore import Qt
from create_database import open_meet_setup  # Correctly import the open_meet_setup function from create_database
from import_json import ImportJson
from import_txt import ImportData
global_db_file_path = None
global_age_group_birthday = False  # Default value
from resource_path import resource_path


class MeetManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Meet Systems Track Manager")
        self.setGeometry(100, 100, 1280, 720)

        # Set the window icon using your custom logo
        logo_path = resource_path("images/ms.png")  # Replace with the actual path to your logo
        self.setWindowIcon(QIcon(logo_path))

        # Background image
        self.image_path = resource_path("images/britanie.png")
        self.pixmap = QPixmap(self.image_path)
        self.label = QLabel(self)
        self.label.setPixmap(self.pixmap)
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.label.setScaledContents(True)

        # Open Database Label
        self.open_db_label = QLabel("No Database Opened", self)
        self.open_db_label.setStyleSheet("color: white; font-size: 16px;")
        self.open_db_label.adjustSize()
        self.center_label_on_menu_bar()

        # Menu bar
        menubar = self.menuBar()
        menubar.setStyleSheet(
            "QMenuBar { background-color: #333; color: white; } QMenuBar::item { background-color: #333; }")
        file_menu = menubar.addMenu('File')

        # Division dropdown menu
        division_menu = menubar.addMenu('Division')

        # Add "Division Templates" option
        division_templates_action = QAction('Setup Divisions', self)
        division_templates_action.triggered.connect(self.division_templates)
        division_menu.addAction(division_templates_action)

        event_menu = menubar.addMenu('Events')
        event_action = QAction('Event Setup', self)
        event_action.triggered.connect(self.event_setup)
        event_menu.addAction(event_action)


        # Add other menus (File, Meet Setup, Athletes, Teams, etc.)
        meet_setup_action = QAction('Meet Setup', self)
        meet_setup_action.triggered.connect(self.open_meet_setup)
        file_menu.addAction(meet_setup_action)

        open_db_action = QAction('Open Database', self)
        open_db_action.triggered.connect(self.open_database)
        file_menu.addAction(open_db_action)

        athletes_action = QAction('Athletes', self)
        athletes_action.triggered.connect(self.open_athletes)
        file_menu.addAction(athletes_action)

        teams_action = QAction('Teams', self)
        teams_action.triggered.connect(self.open_teams)
        file_menu.addAction(teams_action)

        purge_action = QAction('Purge Database', self)
        purge_action.triggered.connect(self.purge_data_base)
        file_menu.addAction(purge_action)

        import_action = QAction('Import', self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

    def event_setup(self):
        """Open the Events dialog if the database is open."""
        print("Event window opened")

        if global_db_file_path:
            from events_window import show_event_window  # Importing show_event_window
            show_event_window(global_db_file_path)
        else:
            print("No database is currently open. Please open a database first.")
            QMessageBox.warning(self, "Database Not Open", "Please open a database before accessing Events.")
    def division_templates(self):
        """
        Open the Division Templates dialog if the database is open.
        """
        print("Division Templates selected")

        # Check if the global database file path is set
        if global_db_file_path:
            import divisions
            divisions.show_divisions_window(global_db_file_path)

        else:
            # Inform the user that the database is not open
            print("No database is currently open. Please open a database first.")
            QMessageBox.warning(self, "Database Not Open",
                                "Please open a database before accessing Division Templates.")

    # def division_templates(self):
    #
    #     """
    #     Open the Division Templates dialog.
    #     """
    #     print("Division Templates selected")
    #     dialog = DivisionTemplatesDialog(self)  # Pass the parent window if needed
    #     if dialog.exec():
    #         print("Division Templates dialog closed.")
    def purge_data_base(self):
        """
        Purge data from athletes, divisions, and teams tables except for rows with 'Unattached'.
        """
        if not global_db_file_path:
            QMessageBox.warning(self, "Warning", "Please open a database first.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Purge",
            "This will delete all data in the Athletes, Divisions, and Teams tables except for 'Unattached'. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(global_db_file_path)
                cursor = conn.cursor()

                # Purge athletes table
                cursor.execute("DELETE FROM athletes")

                # Purge events table
                # Delete all rows from the events table
                cursor.execute("DELETE FROM events")

                # Reset the auto-increment counter for the events table
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='events'")

                # Purge divisions table
                cursor.execute("DELETE FROM divisions_age_group")

                # Purge divisions table
                cursor.execute("DELETE FROM divisions_non_age_groups")

                # Purge teams table except for 'Unattached'
                cursor.execute("""
                    DELETE FROM teams
                    WHERE team_name != 'Unattached'
                """)

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Purge Complete", "Data purged successfully, except for 'Unattached'.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to purge data. Error: {str(e)}")

    def resizeEvent(self, event):
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.label.setPixmap(self.pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.center_label_on_menu_bar()

    def center_label_on_menu_bar(self):
        label_width = self.open_db_label.width()
        window_width = self.width()
        menu_bar_height = self.menuBar().height()
        new_x = (window_width - label_width) // 2
        self.open_db_label.setGeometry(new_x, menu_bar_height + 5, label_width, 30)

    def open_database(self):
        global global_db_file_path, global_age_group_birthday
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Database", "", "SQLite Database (*.db)")
        if file_path:

            try:
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                cursor.execute("SELECT setting_value FROM settings WHERE setting_name = 'use_age_group_birthday'")
                result = cursor.fetchone()
                if result:
                    global_age_group_birthday = result[0] == 'True'
                else:
                    global_age_group_birthday = False

                conn.close()
                self.open_db_label.setText(f"Opened Database: {os.path.basename(file_path)}")
                self.open_db_label.adjustSize()
                self.center_label_on_menu_bar()
                global_db_file_path = file_path

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to open the database. Error: {str(e)}")

    def import_data(self):
        if global_db_file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "Text or CSV Files (*.txt *.csv *.json)")
            if file_path:
                file_extension = os.path.splitext(file_path)[1].lower()
                try:
                    if file_extension == '.json':
                       importer = ImportJson(global_db_file_path)
                       importer.import_file(file_path)
                    elif file_extension in ['.txt', '.csv']:
                        importer = ImportData(global_db_file_path)
                        importer.import_file(file_path)

                    QMessageBox.information(self, "Import", "Data imported successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import data: {e}")
            else:
                QMessageBox.warning(self, "Import Cancelled", "No file selected.")
        else:
            QMessageBox.warning(self, "Warning", "Please open a database first.")

    def open_meet_setup(self):
        open_meet_setup(self)

    def open_athletes(self):
        if global_db_file_path:
            from athletes import AthletesWindow
            athletes_window = AthletesWindow(global_db_file_path, global_age_group_birthday)
            athletes_window.exec()
        else:
            QMessageBox.warning(self, "Warning", "Please open a database first.")

    def open_teams(self):
        if global_db_file_path:
            import teams
            teams.show_teams_window(global_db_file_path)
        else:
            QMessageBox.warning(self, "Warning", "Please open a database first.")




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MeetManager()
    ex.show()
    sys.exit(app.exec())
