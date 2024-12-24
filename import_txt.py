import sqlite3
import csv
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
import sys


class ImportData:
    def __init__(self, db_file_path):
        self.db_file_path = db_file_path

    def connect_db(self):
        """ Connect to the SQLite database. """
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            print(f"Failed to connect to the database: {e}")
            sys.exit(1)

    def import_file(self, file_path):
        """ Import data from the .txt or .csv file into the athletes and teams table. """
        try:
            with open(file_path, newline='', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                conn = self.connect_db()
                cursor = conn.cursor()

                for row in reader:
                    membership_number = row[21] if len(row) > 21 else ""  # Extract membership number if present

                    if row[0] == "I":  # Data related to athletes (I records)
                        self.insert_or_update_athlete_data(cursor, row, membership_number)
                        self.insert_team_data(cursor, row)
                    elif row[0] == "D":  # Data related to athletes (D records)
                        self.insert_or_update_athlete_data(cursor, row,
                                                           membership_number)  # Use same insert for D records
                        self.insert_team_data(cursor, row)

                conn.commit()
                conn.close()

            print(f"Data from {file_path} imported successfully.")
        except Exception as e:
            print(f"Failed to import data: {e}")

    def insert_or_update_athlete_data(self, cursor, row, membership_number):
        """ Insert athlete data into the athletes table, or update if it exists, including the membership number. """
        try:
            # Parsing athlete-related data from the row
            last_name = row[1]
            first_name = row[2]
            middle_initials = row[3]
            gender = row[4]
            dob = row[5]
            team_code = row[6]
            team_name = row[7]
            bib_number = row[22] if len(row) > 22 else ""  # Extract bib number if present

            # Check if the team exists in the team table
            cursor.execute("SELECT id FROM teams WHERE team_code = ?", (team_code,))
            team = cursor.fetchone()

            if team:
                team_id = team[0]
            else:
                # Insert team if it doesn't exist
                cursor.execute("INSERT INTO teams (team_name, team_code) VALUES (?, ?)", (team_name, team_code))
                team_id = cursor.lastrowid

            # Check if the athlete already exists (avoid duplicates)
            cursor.execute("""
                SELECT id, membership_number FROM athletes WHERE last_name = ? AND first_name = ? AND team_code = ?
            """, (last_name, first_name, team_code))
            athlete = cursor.fetchone()

            if athlete:
                # If athlete exists, update the membership number if it's not already there or needs updating
                existing_membership_number = athlete[1]
                if membership_number and (
                        not existing_membership_number or existing_membership_number != membership_number):
                    cursor.execute("""
                        UPDATE athletes
                        SET membership_number = ?
                        WHERE last_name = ? AND first_name = ? AND team_code = ?
                    """, (membership_number, last_name, first_name, team_code))
                    print(f"Updated membership number for {first_name} {last_name}.")
                else:
                    print(f"Athlete {first_name} {last_name} already exists with membership number. Skipping update.")
            else:
                # Insert athlete into the athletes table if they don't exist
                cursor.execute("""
                    INSERT INTO athletes (bib_number, last_name, first_name, middle_initials, gender, dob, team_code, team_name, membership_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (bib_number, last_name, first_name, middle_initials, gender, dob, team_code, team_name,
                      membership_number))
                print(f"Inserted new athlete {first_name} {last_name}.")

        except sqlite3.Error as e:
            print(f"Failed to insert or update athlete data: {e}")
            raise

    def insert_team_data(self, cursor, row):
        """ Insert team data into the teams table, avoiding duplicates. """
        try:
            team_code = row[6]
            team_name = row[7]

            # Check if the team already exists (avoid duplicates)
            cursor.execute("SELECT id FROM teams WHERE team_code = ?", (team_code,))
            team = cursor.fetchone()

            if team:
                print(f"Team {team_name} with code {team_code} already exists. Skipping insert.")
            else:
                # Insert team into the team table
                cursor.execute("INSERT INTO teams (team_name, team_code) VALUES (?, ?)", (team_name, team_code))
                print(f"Inserted new team {team_name}.")

        except sqlite3.Error as e:
            print(f"Failed to insert team data: {e}")
            raise


def run_import():
    app = QApplication(sys.argv)

    # File selection dialog for database
    db_file_path, _ = QFileDialog.getOpenFileName(None, "Select Database", "", "SQLite Database (*.db)")

    if db_file_path:
        import_data = ImportData(db_file_path)

        # File selection dialog for importing .txt or .csv file
        file_path, _ = QFileDialog.getOpenFileName(None, "Import Data", "", "Text or CSV Files (*.txt *.csv)")

        if file_path:
            try:
                import_data.import_file(file_path)
                QMessageBox.information(None, "Import", f"Data imported successfully from {file_path}")
            except Exception as e:
                QMessageBox.critical(None, "Import Error", f"Failed to import data: {e}")
        else:
            print("Import canceled.")
    else:
        print("Database selection canceled.")

    sys.exit(app.exec())


if __name__ == '__main__':
    run_import()
