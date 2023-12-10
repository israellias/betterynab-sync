import pandas as pd
import sys
import json
from datetime import datetime
from pytz import timezone
import json
import csv
from datetime import datetime


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


if len(sys.argv) < 2:
    print("Please provide the input JSON filename as a command-line argument.")
    sys.exit(1)

input_filename = sys.argv[1]

# Read the JSON file
with open(input_filename, "r") as file:
    data = json.load(file)


# Create a CSV file and write the header
with open("ynab.csv", "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Date", "Amount", "Payee"])

    # Loop through the binnacles and movements
    for bin in data["result"]["binnacles"]:
        for movement in bin["movements"]:
            date_str = movement["ledger_datetime"][:10]
            date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            amount = movement["amount"]["fraction"].replace(".", "")
            payee = movement["description"] or movement["metadata"]["description"]

            csv_writer.writerow([date, amount, payee])

print(f"CSV file ynab.csv has been created successfully.")
