import csv
import json

# Step 1: Open the CSV file and read its contents
csv_file = 'events4.csv'
json_file = 'json/events4.json'

data = []

with open(csv_file, mode='r') as file:
    # Step 2: Read the CSV file
    csv_reader = csv.DictReader(file)

    # Step 3: Convert each row into a dictionary and add to the list
    for row in csv_reader:
        data.append(row)

# Step 4: Write the data to a JSON file
with open(json_file, mode='w') as file:
    json.dump(data, file, indent=4)

print("CSV file has been converted to JSON successfully!")
