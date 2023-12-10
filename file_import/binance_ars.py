import csv
import json
import datetime
import sys
from decimal import Decimal

# Verifica si se proporcionó el nombre del archivo JSON como argumento
if len(sys.argv) < 2:
    print("Por favor, proporciona el nombre del archivo JSON como argumento.")
    sys.exit(1)

json_file = sys.argv[1]

# Lee el archivo JSON
with open(json_file, "r") as file:
    data = json.load(file)

# Filtra los datos por orderStatus = 4
filtered_data = [item for item in data["data"] if item["orderStatus"] == 4]


# Función para obtener la fecha en formato dd/mm/yyyy a partir de un timestamp
def get_formatted_date(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp / 1000)
    return date.strftime("%d/%m/%Y")


# Función para formatear el monto con la cantidad de decimales adecuada según la moneda
def format_amount(amount, fiat=None, decimals=None):
    if decimals:
        return round(amount, decimals)

    if fiat in ["USD", "USDT", "BOB"]:
        return round(amount, 2)
    else:
        return int(amount)


# Prepara los datos para el archivo CSV
csv_data = []
for item in filtered_data:
    trade_type = item["tradeType"]
    amount = Decimal(item["amount"])
    asset = item["asset"]
    total_price = Decimal(item["totalPrice"])
    fiat = item["fiat"]
    username = item["buyerNickname"] if trade_type == "SELL" else item["sellerNickname"]
    create_time = get_formatted_date(item["createTime"])
    commission = Decimal(item.get("commission", 0))  # Get commission or default to 0

    memo = f"{trade_type} {format_amount(amount, fiat)} {asset} with {format_amount(total_price, fiat)} {fiat} ({username})"

    if trade_type == "BUY":
        inflow = format_amount(total_price, fiat)
        outflow = ""
    else:
        inflow = ""
        outflow = format_amount(amount - commission, fiat)
        memo = f"[TC:{format_amount(Decimal(item['price']), decimals=2)}]"

    payee = "Transfer:Zinli" if trade_type == "BUY" else "Transfer:ARS"
    csv_data.append([create_time, payee, outflow, inflow, memo])

# Escribe los datos en un archivo CSV
csv_file = "ynab.csv"
with open(csv_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Payee", "Outflow", "Inflow", "Memo"])
    writer.writerows(csv_data)

print(f"Archivo CSV '{csv_file}' generado exitosamente.")
