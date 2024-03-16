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

    with open(output_file, "w", newline="") as output:
        csv_writer = csv.writer(output, delimiter=",")
        csv_writer.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])
        for row in csv_reader:
            if row[0] == "":  # Ignora líneas vacías
                continue
            date = row[0]
            memo = row[1]
            outflow = row[2].replace(",", "").replace("-", "")
            inflow = row[3].replace(",", "")
            if outflow != "":
                outflow = float(outflow)
                inflow = ""
            else:
                inflow = float(inflow)
                outflow = ""
            if "ITF" in memo:
                payee = "Banca"
            elif "Retiro" in memo:
                payee = "Transfer : Wallet ISR"
            else:
                payee = ""

            csv_writer.writerow([date, payee, "", memo, outflow, inflow])

print(f"El archivo {output_file} ha sido creado con éxito.")
