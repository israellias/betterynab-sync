import json
import os

from bisa.config import BisaConfig
from bisa.converter import BisaConverter
from bisa.exporter import BisaExporter
from bisa.pipeline import BisaPipeline

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSACTIONS_PATH = os.path.join(MODULE_DIR, "transactions.json")
EXPORT_PATH = os.path.join(MODULE_DIR, "export.csv")

__all__ = [
    "BisaConfig",
    "BisaConverter",
    "BisaExporter",
    "BisaPipeline",
    "load_pending_transactions",
    "import_to_ynab",
    "get_bob_categories",
    "get_last_balance",
    "get_ynab_balance",
]


def load_pending_transactions() -> list[dict]:
    """Load transactions from bisa/transactions.json."""
    if not os.path.exists(TRANSACTIONS_PATH):
        raise FileNotFoundError(f"No pending transactions file found at {TRANSACTIONS_PATH}")
    with open(TRANSACTIONS_PATH, "r") as f:
        return json.load(f)


def import_to_ynab(transactions: list[dict]) -> dict:
    """Bulk import transactions to YNAB. Returns {imported, duplicates}."""
    config = BisaConfig()
    from services.ynab_importer import YNABImporter
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.import_transactions(transactions)


def get_last_balance() -> float:
    """Read the last 'Saldo Bs' value from bisa/export.csv."""
    import csv

    if not os.path.exists(EXPORT_PATH):
        raise FileNotFoundError(f"No export file found at {EXPORT_PATH}")

    last_balance = None
    with open(EXPORT_PATH, "r", encoding="latin-1") as f:
        reader = csv.reader(f, delimiter=",")
        # Skip header rows until we find the "Fecha" column
        for row in reader:
            if len(row) > 0 and row[0].startswith("Fecha"):
                break
        # Read data rows — balance is in the 5th column (index 4)
        for row in reader:
            if not row[0]:
                continue
            balance_raw = row[4].replace(",", "") if len(row) > 4 else ""
            if balance_raw:
                last_balance = float(balance_raw)
    if last_balance is None:
        raise ValueError("No balance found in export CSV.")
    return last_balance


def get_bob_categories() -> list[dict]:
    """Fetch active categories from BOB Budget via YNAB API.

    Returns list of {"id": ..., "name": ...} dicts.
    """
    from dotenv import load_dotenv
    from services._ynab_connection import YNABClient

    load_dotenv()
    client = YNABClient()
    budgets = client.get_budgets()
    bob = next((b for b in budgets if b.name == "BOB Budget"), None)
    if not bob:
        raise ValueError("BOB Budget not found in YNAB.")
    categories = client.get_categories(bob.id)
    return [{"id": c.id, "name": c.name} for c in categories if not c.hidden and not c.deleted]


def get_ynab_balance() -> dict:
    """Get YNAB balance for this module's account.

    Returns dict with balance, cleared_balance, uncleared_balance (milliunit × 1000).
    """
    from dotenv import load_dotenv

    load_dotenv()
    config = BisaConfig()
    from services.ynab_importer import YNABImporter
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.get_account_balance()
