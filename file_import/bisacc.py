import csv
import sys

if len(sys.argv) != 2:
    print(
        "Por favor, proporcione el nombre del archivo a procesar como argumento en la línea de comandos."
    )
    sys.exit()

input_file = sys.argv[1]
output_file = "ynab.csv"

with open(input_file, "r", encoding="latin-1") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    next(csv_reader)  # Ignora la primera línea
    next(csv_reader)  # Ignora la segunda línea
    next(csv_reader)  # Ignora la tercera línea
    next(csv_reader)  # Ignora la cuarta línea
    next(csv_reader)  # Ignora la quinta línea
    next(csv_reader)  # Ignora la sexta línea
    next(csv_reader)  # Ignora la septima línea
    next(csv_reader)  # Ignora la octava línea
    next(csv_reader)  # Ignora la novena línea
    next(csv_reader)  # Ignora la decima línea

    with open(output_file, "w", newline="") as output:
        csv_writer = csv.writer(output, delimiter=",")
        csv_writer.writerow(["Date", "Payee", "Category", "Memo", "Amount"])
        for row in csv_reader:
            if row[0] == "":  # Ignora líneas vacías
                continue
            date = row[0]
            memo = row[5]

            # Clean original_amount - handle both US$ and Bs prefixes
            original_amount = row[6].replace(",", "")
            original_amount = original_amount.replace("US$ ", "").replace("Bs ", "")

            # Clean amount
            amount = row[7].replace(",", "").replace("Bs ", "")

            # Process amount if it's not empty
            if amount and amount != "":
                try:
                    amount = float(amount) * -1
                except ValueError:
                    print(
                        f"Error: No se pudo convertir '{row[7]}' a un número. Usando 0 para la transacción: {memo}"
                    )
                    amount = 0  # Set to 0 instead of skipping

            # Process original_amount if amount is 0 and original_amount is not empty
            if (
                (amount == 0 or not amount)
                and original_amount
                and original_amount != ""
            ):
                try:
                    amount = float(original_amount) * 6.97 * -1
                except ValueError:
                    print(
                        f"Error: No se pudo convertir '{row[6]}' a un número. Usando 0 para la transacción: {memo}"
                    )
                    amount = 0  # Set to 0 instead of skipping

            # Handle payee based on transaction description
            if "CUOTA ANUAL" in memo:
                payee = "Banca"
            elif "Retiro" in memo:
                payee = "Transfer : Wallet ISR"
            else:
                payee = ""

            csv_writer.writerow([date, payee, "", memo, amount])

print(f"El archivo {output_file} ha sido creado con éxito.")
