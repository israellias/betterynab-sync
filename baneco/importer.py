from dotenv import load_dotenv

from services._ynab_connection import YNABClient

load_dotenv()


class YNABImporter:
    def __init__(self, budget_name: str, account_id: str):
        self._budget_name = budget_name
        self._account_id = account_id
        self._client = YNABClient()
        self._budget_id = None

    @property
    def budget_id(self) -> str:
        """Resolve budget name to ID (cached after first call)."""
        if self._budget_id is None:
            budgets = self._client.get_budgets()
            budget = next(
                (b for b in budgets if b.name == self._budget_name),
                None,
            )
            if not budget:
                raise ValueError(f'Budget "{self._budget_name}" not found in YNAB.')
            self._budget_id = budget.id
        return self._budget_id

    def get_last_transaction_date(self) -> str | None:
        """Find the most recent transaction date for this account."""
        transactions = self._client.get_transactions(self.budget_id)
        account_txns = [t for t in transactions if t.account_id == self._account_id]

        if not account_txns:
            return None

        return max(t.date for t in account_txns)

    def import_transactions(self, transactions: list) -> dict:
        """Bulk import transactions to YNAB. Returns import summary."""
        if not transactions:
            print("No transactions to import.", flush=True)
            return {"imported": 0, "duplicates": 0}

        result = self._client.import_transactions(self.budget_id, transactions)

        duplicates = len(result.get("duplicate_import_ids", []))
        imported = len(transactions) - duplicates

        print(
            f"Imported {imported} transactions ({duplicates} duplicates skipped).",
            flush=True,
        )

        return {"imported": imported, "duplicates": duplicates}
