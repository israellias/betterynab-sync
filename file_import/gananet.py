import sys

import pandas as pd

if len(sys.argv) != 2:
    print("Usage: python convert_excel_to_csv.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]

# Load the Excel file, skipping the first 10 rows
df = pd.read_excel(file_path, skiprows=8)

# Rename the columns to meaningful names
df.columns = [
    "Date",
    "Time",
    "Transaction_Type",
    "Transaction_Number",
    "Memo",
    "Outflow",
    "Inflow",
    "Balance",
]

# Drop any rows where 'Date' is NaN (if there are any)
df.dropna(subset=["Date"], inplace=True)

# Keep only relevant columns and rename them to match the desired output format
df = df[["Date", "Memo", "Outflow", "Inflow"]]
df["Payee"] = None  # Add a Payee column with None values
df["Category"] = None  # Add a Category column with None values

# Reorder the columns to match the desired output
df = df[["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"]]

# Save the cleaned data to a CSV file
output_csv_path = "ynab.csv"
df.to_csv(output_csv_path, index=False)
