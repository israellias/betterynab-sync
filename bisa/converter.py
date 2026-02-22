import csv
import hashlib


class BisaConverter:
    def convert(self, csv_path: str, account_id: str) -> list:
        """Parse BISA CSV export and return YNAB API transaction dicts."""
        transactions = []

        with open(csv_path, "r", encoding="latin-1") as f:
            reader = csv.reader(f, delimiter=",")

            # Skip header rows until we find the "Fecha" column
            for row in reader:
                if len(row) > 0 and row[0].startswith("Fecha"):
                    break

            for row in reader:
                if not row[0]:
                    continue

                date_raw = row[0]  # dd/mm/yyyy
                memo = row[1]
                outflow_raw = row[2].replace(",", "").replace("-", "")
                inflow_raw = row[3].replace(",", "")

                # Parse amount in milliunit format
                if outflow_raw:
                    amount = -int(float(outflow_raw) * 1000)
                else:
                    amount = int(float(inflow_raw) * 1000)

                # Convert date from dd/mm/yyyy to yyyy-mm-dd
                parts = date_raw.split("/")
                iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"

                # Generate import_id using hash for dedup
                hash_input = f"{iso_date}:{amount}:{memo}"
                hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12]
                import_id = f"BISA:{hash_val}:{iso_date}"

                transactions.append(
                    {
                        "account_id": account_id,
                        "date": iso_date,
                        "amount": amount,
                        "payee_name": "",
                        "memo": memo,
                        "import_id": import_id,
                        "cleared": "cleared",
                        "approved": False,
                    }
                )

        return transactions
