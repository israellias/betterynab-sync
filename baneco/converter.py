import csv


class BanecoConverter:
    MONTHS = {
        "ene": "01", "feb": "02", "mar": "03", "abr": "04",
        "may": "05", "jun": "06", "jul": "07", "ago": "08",
        "sep": "09", "oct": "10", "nov": "11", "dic": "12",
    }

    @staticmethod
    def parse_date(fecha_str: str) -> str:
        """Convert '10/Feb/2026' to '2026-02-10'."""
        parts = fecha_str.strip().split("/")
        day = parts[0].zfill(2)
        month = BanecoConverter.MONTHS[parts[1].lower()]
        year = parts[2]
        return f"{year}-{month}-{day}"

    def _parse_row(self, row: dict) -> dict:
        """Parse a single Baneco CSV row into a normalized dict."""
        iso_date = self.parse_date(row["Fecha"])
        amount = float(row["Monto"].replace(",", "."))
        memo = row["Nota"].strip() if row["Nota"].strip() else row["Transaccion"]
        nro_trn = row["Nro Trn./Cheque"].strip()

        return {
            "date": iso_date,
            "amount": amount,
            "memo": memo,
            "nro_trn": nro_trn,
        }

    def convert(self, csv_path: str, account_id: str, since_date: str = None) -> list:
        """Parse Baneco CSV and return YNAB API transaction dicts."""
        transactions = []

        with open(csv_path, "r") as f:
            for row in csv.DictReader(f):
                parsed = self._parse_row(row)

                if since_date and parsed["date"] < since_date:
                    continue

                transactions.append({
                    "account_id": account_id,
                    "date": parsed["date"],
                    "amount": int(parsed["amount"] * 1000),
                    "payee_name": "",
                    "memo": parsed["memo"],
                    "cleared": "cleared",
                    "approved": False,
                    "import_id": f"BEC:{parsed['nro_trn']}:{parsed['date']}",
                })

        return transactions

    def to_ynab_csv(self, csv_path: str, output_path: str = "ynab.csv"):
        """Parse Baneco CSV and write YNAB-compatible CSV for manual import."""
        with open(csv_path, "r") as infile, open(output_path, "w", newline="") as outfile:
            reader = csv.DictReader(infile)
            writer = csv.writer(outfile)
            writer.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])

            for row in reader:
                parsed = self._parse_row(row)
                y, m, d = parsed["date"].split("-")
                ynab_date = f"{m}/{d}/{y}"

                if parsed["amount"] < 0:
                    outflow = str(-parsed["amount"])
                    inflow = ""
                else:
                    outflow = ""
                    inflow = str(parsed["amount"])

                writer.writerow([ynab_date, "", "", parsed["memo"], outflow, inflow])

        print(f"Converted {csv_path} -> {output_path}", flush=True)
