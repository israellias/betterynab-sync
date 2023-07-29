import pandas as pd
import sys

# Verifica que se haya proporcionado una ruta de archivo
if len(sys.argv) != 2:
    print("Uso: python convert_excel_to_csv.py <ruta_del_archivo>")
    sys.exit(1)

# Lee la ruta del archivo del primer argumento
ruta_archivo = sys.argv[1]

# Lee el archivo de Excel saltando la primera fila
df = pd.read_excel(ruta_archivo, skiprows=1)

# Función de formateo personalizada
def formato_num(valor):
    if isinstance(valor, str):
        return valor.replace(",", "")
    else:
        return valor

# Aplica la función de formateo a las columnas "Débitos" y "Créditos"
df[['Débitos', 'Créditos']] = df[['Débitos', 'Créditos']].applymap(formato_num)

# Filtra los datos que deseas mantener
df = df[['Fecha', 'Débitos', 'Créditos', 'Referencia', 'Adicionales']]
df['Payee'] = ""
df['Category'] = ""
df['Memo'] = df['Referencia'].str.strip() + "|" + df['Adicionales'].str.strip()
df = df[['Fecha', 'Débitos', 'Créditos', 'Memo']]
df = df.rename(columns={'Fecha': 'Date', 'Débitos': 'Outflow', 'Créditos': 'Inflow'})

# Guarda el archivo CSV como "ynab.csv"
df.to_csv("ynab.csv", index=False)

print("Archivo CSV generado correctamente.")
