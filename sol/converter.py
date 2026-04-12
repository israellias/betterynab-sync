import hashlib
import re

import PyPDF2


class SolConverter:
    def convert(self, pdf_path: str, account_id: str, since_date: str = None) -> list:
        """Parse Banco Sol PDF extract and return YNAB API transaction dicts."""
        raw_transactions = self._extract_transactions(pdf_path)
        transactions = []

        for txn in raw_transactions:
            if since_date and txn["date"] < since_date:
                continue

            # Amount is already signed: negative for debits, positive for credits
            amount = int(txn["amount"] * 1000)

            # Build memo from description + glosa/recipient
            memo = txn["description"]
            if txn.get("detail"):
                memo = f"{memo} | {txn['detail']}"

            # Generate import_id for dedup
            hash_input = f"{txn['date']}:{amount}:{txn['time']}:{memo}"
            hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12]
            import_id = f"SOL:{hash_val}:{txn['date']}"

            transactions.append({
                "account_id": account_id,
                "date": txn["date"],
                "amount": amount,
                "payee_name": "",
                "memo": memo,
                "import_id": import_id,
                "cleared": "cleared",
                "approved": False,
            })

        return transactions

    def _extract_transactions(self, pdf_path: str) -> list:
        """Extract transactions from Banco Sol PDF extract.

        Actual PDF text extraction format (PyPDF2):
            Line 1: "DD-MM-YYYY"
            Line 2: "HH:MMDescription text [+-]Bs X.XX Bs X.XX"
            Line 3+: Detail lines (recipient, cuenta, glosa)

        The time and description are joined without space on the same line.
        """
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

        lines = full_text.split("\n")
        transactions = []

        # Pattern for date-only line
        date_pattern = re.compile(r'^(\d{2}-\d{2}-\d{4})$')

        # Pattern for time+description+amount+balance line
        # e.g. "18:55Transacción ACH -Bs 471.69 Bs 0.00"
        # or   "18:51Transf. cuentas SolNet +Bs 2.30 Bs 466.69"
        txn_line_pattern = re.compile(
            r'^(\d{2}:\d{2})'           # Time HH:MM
            r'(.+?)\s+'                 # Description
            r'([+-]Bs\s*[\d,]+\.?\d*)'  # Amount (+Bs or -Bs)
            r'\s+Bs\s*[\d,]+\.?\d*'     # Balance
        )

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            date_match = date_pattern.match(line)

            if date_match:
                date_raw = date_match.group(1)  # DD-MM-YYYY
                day, month, year = date_raw.split("-")
                iso_date = f"{year}-{month}-{day}"

                # Next line should have time + description + amount
                i += 1
                if i >= len(lines):
                    break

                txn_line = lines[i].strip()
                txn_match = txn_line_pattern.match(txn_line)

                if txn_match:
                    time_str = txn_match.group(1)
                    description = txn_match.group(2).strip()
                    amount_str = txn_match.group(3).strip()
                    amount = self._parse_amount(amount_str)
                    i += 1

                    # Collect detail lines (recipient, cuenta, glosa)
                    detail_parts = []
                    while i < len(lines):
                        next_line = lines[i].strip()
                        # Stop if we hit another transaction date
                        if date_pattern.match(next_line):
                            break
                        # Skip empty lines
                        if not next_line:
                            i += 1
                            continue
                        # Skip page headers/footers
                        if self._is_header_line(next_line):
                            i += 1
                            continue
                        detail_parts.append(next_line)
                        i += 1

                    detail = " | ".join(detail_parts) if detail_parts else ""

                    transactions.append({
                        "date": iso_date,
                        "time": time_str,
                        "description": description,
                        "amount": amount,
                        "detail": detail,
                    })
                else:
                    i += 1
            else:
                i += 1

        return transactions

    @staticmethod
    def _is_header_line(line: str) -> bool:
        """Check if a line is a PDF header/footer to skip."""
        if "Fonosol" in line or "onosol" in line:
            return True
        if "www.bancosol" in line or "bancosol.com" in line:
            return True
        if "supervisada por ASFI" in line:
            return True
        if re.match(r'^\d+\s+\w+\s+de\s+\d{4}\s*\|', line):
            return True
        if line.startswith("Extracto de Caja"):
            return True
        if line.startswith("(Bolivianos)"):
            return True
        if "Fecha y hora" in line:
            return True
        if line.startswith("Titular:") or line.startswith("Estado:"):
            return True
        if line.startswith("Cuenta:") or line.startswith("Producto:"):
            return True
        if "Administración:" in line:
            return True
        if re.match(r'^\d{2}-\d{2}-\d{4}\s+al\s+\d{2}-\d{2}-\d{4}', line):
            return True
        return False

    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """Parse '+Bs 5.00' or '-Bs 471.69' or '+Bs 25,000.00' to float."""
        cleaned = amount_str.replace("Bs", "").replace(" ", "").replace(",", "")
        if cleaned.startswith("+"):
            return float(cleaned[1:])
        elif cleaned.startswith("-"):
            return -float(cleaned[1:])
        return float(cleaned)
