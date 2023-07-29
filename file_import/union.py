import pandas as pd
import sys

# Verifica que se haya proporcionado una ruta de archivo
if len(sys.argv) != 2:
    print("Uso: python convert_excel_to_csv.py <ruta_del_archivo>")
    sys.exit(1)

# Lee la ruta del archivo del primer argumento
ruta_archivo = sys.argv[1]

# Lee el archivo de Excel
df = pd.read_excel(ruta_archivo, header=15)

# Encuentra el índice de la fila que contiene "Total Créditos:"
index_total_creditos = df[df['Fecha Movimiento'] == 'Total Créditos:'].index[0]

# Filtra los datos que deseas mantener
df = df.iloc[:index_total_creditos-1]
df = df[['Fecha Movimiento', 'Monto\n', 'Descripción']]
# df['Outflow'] = df['Monto\n'].apply(lambda x: abs(float(x.replace(',', ''))) if float(x.replace(',', '')) < 0 else '')
# df['Inflow'] = df['Monto\n'].apply(lambda x: float(x.replace(',', '')) if float(x.replace(',', '')) > 0 else '')
df['Amount'] = df['Monto\n']
# df = df[['Fecha Movimiento', 'Outflow', 'Inflow', 'Descripción']]
df = df[['Fecha Movimiento', 'Amount', 'Descripción']]
df = df.rename(columns={'Fecha Movimiento': 'Date', 'Descripción': 'Memo'})

# Guarda el archivo CSV como "ynab.csv"
df.to_csv("ynab.csv", index=False)

print("Archivo CSV generado correctamente.")
