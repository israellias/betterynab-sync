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

    def get_account_balance(self) -> dict:
        """Get balance for this importer's account.

        Returns dict with cleared_balance, uncleared_balance, balance
        (all in milliunit × 1000 format).
        """
        accounts = self._client.get_accounts(self.budget_id)
        account = next(
            (a for a in accounts if a["id"] == self._account_id),
            None,
        )
        if not account:
            raise ValueError(
                f'Account "{self._account_id}" not found in budget "{self._budget_name}".'
            )
        return {
            "cleared_balance": account["cleared_balance"],
            "uncleared_balance": account["uncleared_balance"],
            "balance": account["balance"],
        }

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
