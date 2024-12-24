def event_setup(self):
    """Open the Events dialog if the database is open."""
    print("Event window opened")
    if global_db_file_path:
        show_event_window(global_db_file_path)
    else:
        print("No database is currently open. Please open a database first.")
        QMessageBox.warning(self, "Database Not Open", "Please open a database before accessing Events.")
from events_window import show_event_window  # Importing show_event_window