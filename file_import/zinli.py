import pdfplumber
import csv
import sys

# Verifica que se haya proporcionado una ruta de archivo
if len(sys.argv) != 2:
    print("Usage: python convert_pdf_to_csv.py <file_path>")
    sys.exit(1)

# Lee la ruta del archivo PDF del primer argumento
file_path = sys.argv[1]

# Ruta de salida del archivo CSV
output_csv_path = "ynab.csv"

# Opens the PDF file
with pdfplumber.open(file_path) as pdf:
    # Extracts the text from each page
    all_text = ""
    for page in pdf.pages:
        all_text += page.extract_text() + "\n"

    # Extracts the tabular data from the text
    lines = all_text.split("\n")
    data = []
    start_index = 0
    for i, line in enumerate(lines):
        if line.strip() == "Fecha Descripción Monto Referencia":
            start_index = i + 1
            break
    

    for line in lines[start_index:]:
        # Customize this logic based on the structure of your PDF table
        row = line.split()
        if len(row) >= 4:
            date = row[0]
            description = " ".join(row[1:-2])
            reference = row[-1]
            amount = row[-2]
            data.append([date, amount, "", description, reference])

# Modifies the extracted data to match the desired output format
modified_data = []
for row in data:
    date = row[0]
    outflow = row[1].replace("$", "").replace(",", "")[1:] if float(row[1].replace("$", "").replace(",", "")) < 0 else ""
    inflow = row[1].replace("$", "").replace(",", "") if float(row[1].replace("$", "").replace(",", "")) > 0 else ""
    memo = f"{row[3]} {row[4]}" if row[4] else row[3]
    modified_data.append([date, outflow, inflow, memo])

# Writes the modified data to a CSV file
with open(output_csv_path, "w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Date", "Outflow", "Inflow", "Memo"])
    writer.writerows(modified_data)

print("CSV file generated successfully.")
