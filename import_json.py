import sqlite3
import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
import sys
from datetime import datetime


class ImportJson:
    def __init__(self, db_file_path):
        self.db_file_path = db_file_path

    def connect_db(self):
        """ Connect to the SQLite database. """
        try:
            return sqlite3.connect(self.db_file_path)
        except sqlite3.Error as e:
            print(f"Failed to connect to the database: {e}")
            sys.exit(1)

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
            QMessageBox.critical(None, "Database Error", f"Failed to fetch settings: {e}")
            return False

    def import_file(self, file_path):
        """ Import data from the .json file into the athletes, teams, and divisions tables. """
        try:
            use_age_group_birthday = self.get_age_group_birthday_setting()
            print(use_age_group_birthday)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                conn = self.connect_db()
                cursor = conn.cursor()

                # Import divisions data
                divisions_data = data.get("divisions", [])
                for division in divisions_data:
                    self.insert_division_data(cursor, division,use_age_group_birthday)

                # Import team and athlete data
                athletes_data = data.get("athletes", [])
                for athlete in athletes_data:
                    team = athlete.get("team", {})
                    dob = athlete.get("birthdate", "") if use_age_group_birthday else ""
                    age = None

                    # Calculate age if DOB is present and setting is True
                    if dob and use_age_group_birthday:
                        dob_date = datetime.strptime(dob, '%m/%d/%Y')  # Adjust format as needed
                        today = datetime.today()
                        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

                    self.insert_team_data(cursor, team)  # Insert team data
                    self.insert_or_update_athlete_data(cursor, athlete, team, dob, age)  # Insert athlete data with age

                conn.commit()
                conn.close()

            print(f"Data from {file_path} imported successfully.")
        except Exception as e:
            print(f"Failed to import data: {e}")

    def insert_division_data(self, cursor, division, use_age_group_birthday):
        """Insert division data into the divisions table, avoiding duplicates."""

        try:
            print(use_age_group_birthday)
            if not use_age_group_birthday:
                # Non-age-group division data
                division_number = division.get("division_number")
                division_name = division.get("division_name", "")

                # Check if the division already exists in divisions_non_age_groups
                cursor.execute("""
                    SELECT id FROM divisions_non_age_groups 
                    WHERE division_number = ? AND division_name = ?
                """, (division_number, division_name))
                existing_division = cursor.fetchone()

                if existing_division:
                    print(
                        f"Division {division_name} with number {division_number} already exists in non-age-groups. Skipping insert.")
                else:
                    # Insert into divisions_non_age_groups
                    cursor.execute("""
                        INSERT INTO divisions_non_age_groups (division_number, division_name)
                        VALUES (?, ?)
                    """, (division_number, division_name))
                    print(f"Inserted new non-age-group division {division_name} with number {division_number}.")
            else:
                # Age-group division data
                division_number = division.get("division_number")
                division_name = division.get("division_name", "")
                from_age = division.get("from_age")
                to_age = division.get("to_age")

                # Check if the division already exists in divisions_age_group
                cursor.execute("""
                    SELECT id FROM divisions_age_group 
                    WHERE division_number = ? AND division_name = ? AND from_age = ? AND to_age = ?
                """, (division_number, division_name, from_age, to_age))
                existing_division = cursor.fetchone()

                if existing_division:
                    print(
                        f"Division {division_name} with number {division_number} (ages {from_age}-{to_age}) already exists in age-groups. Skipping insert.")
                else:
                    # Insert into divisions_age_group
                    cursor.execute("""
                        INSERT INTO divisions_age_group (division_number, division_name, from_age, to_age)
                        VALUES (?, ?, ?, ?)
                    """, (division_number, division_name, from_age, to_age))
                    print(
                        f"Insertedddd new age-group division {division_name} with number {division_number} (ages {from_age}-{to_age}).")

        except sqlite3.Error as e:
            print(f"Failed to insert division data: {e}")
            raise

    def insert_or_update_athlete_data(self, cursor, athlete, team, dob="", age=None):
        """ Insert athlete data into the athletes table, or update if it exists. """
        try:
            # Extracting athlete-related data from the JSON object
            last_name = athlete.get("lastname")
            first_name = athlete.get("firstname")
            middle_initials = athlete.get("middlename", "")
            gender = athlete.get("gender", "")
            team_code = team.get("team_code", "")
            team_name = team.get("organization_name", "")
            membership_number = athlete.get("membership", "")
            bib_number = ""  # No bib_number in this JSON structure
            if "unattached" in team_name.lower():
                team_name = "Unattached"


            # Skip if last_name or first_name is empty or None
            if not last_name or not first_name:
                print("Skipping athlete with missing first or last name.")
                return

            # Check if the team exists in the team table
            cursor.execute("SELECT id FROM teams WHERE team_code = ?", (team_code,))
            team_record = cursor.fetchone()

            if team_record:
                team_id = team_record[0]
            else:
                # If the team doesn't exist, insert it and get the new team_id
                cursor.execute("INSERT INTO teams (team_name, team_code) VALUES (?, ?)", (team_name, team_code))
                team_id = cursor.lastrowid

            # Check if the athlete already exists
            cursor.execute("""
                SELECT id, membership_number FROM athletes WHERE last_name = ? AND first_name = ? AND team_code = ?
            """, (last_name, first_name, team_code))
            existing_athlete = cursor.fetchone()

            if existing_athlete:
                # Update membership number if necessary
                existing_membership_number = existing_athlete[1]
                if membership_number and (
                        not existing_membership_number or existing_membership_number != membership_number):
                    cursor.execute("""
                        UPDATE athletes
                        SET membership_number = ?
                        WHERE last_name = ? AND first_name = ? AND team_code = ?
                    """, (membership_number, last_name, first_name, team_code))
                    print(f"Updated membership number for {first_name} {last_name}.")
            else:
                # Insert the athlete if they don't exist
                cursor.execute("""
                    INSERT INTO athletes (bib_number, last_name, first_name, middle_initials, gender, dob, age, team_code, team_name, membership_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (bib_number, last_name, first_name, middle_initials, gender, dob, age, team_code, team_name,
                      membership_number))
                print(f"Inserted new athlete {first_name} {last_name}.")

        except sqlite3.Error as e:
            print(f"Failed to insert or update athlete data: {e}")
            raise

    def insert_team_data(self, cursor, team):
        """ Insert team data into the teams table, avoiding duplicates. """
        try:
            team_code = team.get("team_code")
            team_name = team.get("organization_name", "")

            # Check if the team already exists
            cursor.execute("SELECT id FROM teams WHERE team_code = ?", (team_code,))
            existing_team = cursor.fetchone()

            if existing_team:
                print(f"Team {team_name} with code {team_code} already exists. Skipping insert.")
            else:
                # Insert team into the team table
                cursor.execute("INSERT INTO teams (team_name, team_code) VALUES (?, ?)", (team_name, team_code))
                print(f"Inserted new team {team_name} with code {team_code}.")

        except sqlite3.Error as e:
            print(f"Failed to insert team data: {e}")
            raise


def run_import():
    app = QApplication(sys.argv)

    # File selection dialog for database
    db_file_path, _ = QFileDialog.getOpenFileName(None, "Select Database", "", "SQLite Database (*.db)")

    if db_file_path:
        import_data = ImportJson(db_file_path)

        # File selection dialog for importing .json file
        file_path, _ = QFileDialog.getOpenFileName(None, "Import Data", "", "JSON Files (*.json)")

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
