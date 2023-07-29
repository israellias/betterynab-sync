import pandas as pd
import sys
import json
from datetime import datetime
from pytz import timezone


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


if len(sys.argv) < 2:
    print("Please provide the input JSON filename as a command-line argument.")
    sys.exit(1)

input_filename = sys.argv[1]

# Read the JSON file
with open(input_filename, 'r') as file:
    data = json.load(file)

# Extract the required fields from JSON
records = []
for result in data['results']:
    date_str = result['creationDate']
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    date = timezone('UTC').localize(date)
    date = date.astimezone(timezone('America/Argentina/Buenos_Aires')).strftime('%Y-%m-%d')

    amount = result['amount']['fraction'].replace('.', '')
    description = result['description']
    description = remove_prefix(description, 'a ')
    description = remove_prefix(description, 'de ')

    records.append({
        'Date': date,
        'Amount': amount,
        'Payee': description
    })

# Create DataFrame from the records
df = pd.DataFrame(records)

# Export the DataFrame to a CSV file
output_filename = 'ynab.csv'
df.to_csv(output_filename, index=False)

print(f"CSV file '{output_filename}' has been created successfully.")
