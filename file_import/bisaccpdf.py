import csv
import sys
import re
import PyPDF2

if len(sys.argv) != 2:
    print("Usage: python bisaccpdf.py <pdf_file>")
    sys.exit()

input_file = sys.argv[1]
output_file = "ynab.csv"

def parse_date(date_str):
    """Convert DD/MM/YYYY to MM/DD/YYYY for YNAB"""
    try:
        day, month, year = date_str.split('/')
        return f"{month}/{day}/{year}"
    except:
        return date_str

def extract_transactions_from_pdf(pdf_path):
    """Extract transactions from BISA credit card PDF statement"""
    transactions = []

    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        # Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()

        # Split by lines
        lines = full_text.split('\n')

        # Pattern to match transaction lines
        # Format: DD/MM/YYYY Description Dolares Bolivianos
        # Example: 24/07/2025 Comision uso exterior acumulado 0.00 22.58
        date_pattern = r'^(\d{2}/\d{2}/\d{4})\s+'

        # Find where transactions start (after "Fecha Descripción Bolivianos Dolares")
        transaction_section_started = False

        for i, line in enumerate(lines):
            # Skip until we find the transaction header
            if not transaction_section_started:
                if "Fecha" in line and "Descripción" in line and "Bolivianos" in line:
                    transaction_section_started = True
                continue

            # Skip empty lines
            if not line.strip():
                continue

            # Stop if we hit pagination or footer
            if "Página" in line or "PAGA EN CUOTAS" in line or "Total Puntos" in line:
                break

            # Look for lines starting with a date
            date_match = re.match(date_pattern, line.strip())
            if date_match:
                date_str = date_match.group(1)

                # Get the rest of the line after the date
                rest = line[date_match.end():].strip()

                # Extract amounts: Pattern is "Description USD_Amount BS_Amount"
                # Amounts can be at the end, separated by spaces
                # Extract all numbers (including negatives and decimals)
                amounts = re.findall(r'-?[\d,]+\.?\d+', rest)

                if len(amounts) >= 2:
                    # Last two amounts: first is USD, second is Bolivianos
                    usd_str = amounts[-2]
                    bolivianos_str = amounts[-1]

                    # Description is everything except the last two amounts
                    description = rest
                    # Remove amounts from description (from the end)
                    for amount in amounts[-2:]:
                        last_index = description.rfind(amount)
                        if last_index != -1:
                            description = description[:last_index]
                    description = description.strip()

                    transactions.append({
                        'date': date_str,
                        'description': description,
                        'bolivianos': bolivianos_str,
                        'usd': usd_str
                    })

    return transactions

def process_transaction(date_str, description, bolivianos_str, usd_str):
    """Process a single transaction and return formatted data"""
    try:
        amount = float(bolivianos_str.replace(',', ''))

        # Extract memo information
        memo = ""
        payee_name = description

        # Extract USD amounts and put in memo
        usd_match = re.search(r'\(\$US\s*[\d.,]+\)', description)
        if usd_match:
            memo = usd_match.group(0)
            payee_name = description.replace(usd_match.group(0), '').strip()
        elif usd_str and float(usd_str.replace(',', '')) > 0:
            memo = f"($US {usd_str})"

        # Extract installment information (cuotas) and put in memo
        cuota_match = re.search(r'\((\d+/\d+)\)', description)
        if cuota_match:
            if memo:
                memo += f" - Cuota {cuota_match.group(1)}"
            else:
                memo = f"Cuota {cuota_match.group(1)}"
            payee_name = re.sub(r'\s*\(\d+/\d+\)', '', payee_name).strip()

        # Handle different transaction types
        if "pago" in description.lower():
            amount = abs(amount)  # Payments are positive (inflow)
            payee = "Transfer : Credit Card Payment"
        elif "cuota anual" in description.lower() or "mantenimiento" in description.lower():
            amount = -abs(amount)  # Fees are negative (outflow)
            payee = "Banca"
        elif "seguro" in description.lower():
            amount = -abs(amount)  # Insurance is negative (outflow)
            payee = "Seguros"
        elif "interes" in description.lower() or "interés" in description.lower():
            amount = -abs(amount)  # Interest is negative (outflow)
            payee = "Banca"
        else:
            amount = -abs(amount)  # Regular expenses are negative (outflow)
            payee = payee_name

        return {
            'date': parse_date(date_str),
            'payee': payee,
            'memo': memo,
            'amount': amount
        }

    except ValueError as e:
        print(f"Error procesando monto para: {description} - {e}")
        return None

# Extract transactions from PDF
print(f"Leyendo PDF: {input_file}")
raw_transactions = extract_transactions_from_pdf(input_file)
print(f"Encontradas {len(raw_transactions)} líneas de transacción en el PDF")

# Process transactions
transactions = []
for trans in raw_transactions:
    processed = process_transaction(
        trans['date'],
        trans['description'],
        trans['bolivianos'],
        trans['usd']
    )
    if processed:
        transactions.append(processed)

# Write to CSV
with open(output_file, "w", newline="", encoding="utf-8") as output:
    csv_writer = csv.writer(output, delimiter=",")
    csv_writer.writerow(["Date", "Payee", "Category", "Memo", "Amount"])

    for transaction in transactions:
        csv_writer.writerow([
            transaction['date'],
            transaction['payee'],
            "",  # Category
            transaction['memo'],
            transaction['amount']
        ])

print(f"El archivo {output_file} ha sido creado con éxito con {len(transactions)} transacciones.")
