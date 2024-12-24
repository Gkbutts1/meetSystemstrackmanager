import csv
import json
import os
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox


def merge_csv_to_single_json_with_filenames():
    # Initialize the application
    app = QApplication([])

    # Step 1: Open a dialog to select a folder containing CSV files
    folder_path = QFileDialog.getExistingDirectory(
        None, "Select Folder with CSV Files"
    )

    if not folder_path:
        QMessageBox.warning(None, "Warning", "No folder selected!")
        return

    # Step 2: Specify the output JSON file
    json_file, _ = QFileDialog.getSaveFileName(
        None,
        "Save JSON File",
        "",
        "JSON Files (*.json)",
    )

    if not json_file:
        QMessageBox.warning(None, "Warning", "No output file specified!")
        return

    data = {}

    # Step 3: Iterate through all CSV files in the selected folder
    try:
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".csv"):  # Process only CSV files
                csv_file_path = os.path.join(folder_path, file_name)
                file_key = os.path.splitext(file_name)[0]  # File name without extension

                # Read CSV and store data under the file name key
                with open(csv_file_path, mode="r") as file:
                    csv_reader = csv.DictReader(file)
                    data[file_key] = [row for row in csv_reader]

        # Step 4: Write the combined data to the JSON file
        with open(json_file, mode="w") as file:
            json.dump(data, file, indent=4)

        QMessageBox.information(
            None,
            "Success",
            f"CSV files have been merged into a single JSON file successfully!\n\nSaved to: {json_file}",
        )
    except Exception as e:
        QMessageBox.critical(None, "Error", f"An error occurred: {e}")


# Run the function
if __name__ == "__main__":
    merge_csv_to_single_json_with_filenames()
