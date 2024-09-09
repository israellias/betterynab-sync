import csv
import datetime
import json
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


# Función para redondear un número a dos decimales
def round_number(num):
    return round(num, 2)


# Función para formatear el monto con la cantidad de decimales adecuada según la moneda
def format_amount(amount, fiat="USD"):
    if fiat in ["USD", "USDT", "BOB", "EUR"]:
        return round_number(amount)
    else:
        return int(amount)


# Prepara los datos para el archivo CSV
csv_data = []
for item in filtered_data:
    trade_type = item["tradeType"]
    amount = Decimal(item["amount"])
    asset = item["asset"]
    total_price = Decimal(item["totalPrice"])
    price = Decimal(item["price"])
    fiat = item["fiat"]
    username = item["buyerNickname"] if trade_type == "SELL" else item["sellerNickname"]
    create_time = get_formatted_date(item["createTime"])
    commission = Decimal(
        item.get("commission", 0) or 0
    )  # Get commission or default to 0

    memo = f"{trade_type} {format_amount(amount, fiat)} {asset} with {format_amount(total_price, fiat)} {fiat} ({username})"

    if fiat in ("BOB", "EUR", "ARS"):
        memo = "[TC:%s] %s" % (format_amount(price, fiat), memo)

    if trade_type == "BUY" and fiat == "USD":
        payee = "Transfer : Zinli"
    elif trade_type == "SELL" and fiat == "BOB":
        payee = "Transfer : ⚙️ BOB Budget"
    elif trade_type == "SELL" and fiat == "ARS":
        payee = "Transfer : ⚙️ ARS Budget"
    else:
        payee = ""

    if trade_type == "BUY" and "Zinli" in payee:
        inflow = format_amount(total_price, fiat)
        outflow = ""
    elif trade_type == "BUY":
        inflow = format_amount(amount, fiat)
        outflow = ""
    elif trade_type == "SELL":
        inflow = ""
        outflow = format_amount(amount, fiat)

    csv_data.append([create_time, payee, outflow, inflow, memo])

    if commission != 0:
        csv_data.append(
            [
                create_time,
                "Commissions",
                format_amount(commission, fiat),
                "",
                f"Commission for {memo}",
            ]
        )
    if "Zinli" in payee:
        csv_data.append(
            [
                create_time,
                "Commissions",
                "",
                format_amount(amount - total_price, fiat),
                f"Income from exchante rate for {memo}",
            ]
        )

# Escribe los datos en un archivo CSV
csv_file = "ynab.csv"
with open(csv_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Payee", "Outflow", "Inflow", "Memo"])
    writer.writerows(csv_data)

print(f"Archivo CSV '{csv_file}' generado exitosamente.")
