import json
import os

from baneco.config import BanecoConfig
from baneco.converter import BanecoConverter
from baneco.exporter import BanecoExporter
from baneco.importer import YNABImporter
from baneco.pipeline import BanecoPipeline

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_PATH = os.path.join(SCRIPT_DIR, "baneco_transactions.json")

__all__ = [
    "BanecoConfig",
    "BanecoConverter",
    "BanecoExporter",
    "YNABImporter",
    "BanecoPipeline",
    "load_pending_transactions",
    "import_to_ynab",
    "get_bob_categories",
]


def load_pending_transactions() -> list[dict]:
    """Load transactions from baneco_transactions.json."""
    if not os.path.exists(TRANSACTIONS_PATH):
        raise FileNotFoundError(f"No pending transactions file found at {TRANSACTIONS_PATH}")
    with open(TRANSACTIONS_PATH, "r") as f:
        return json.load(f)


def import_to_ynab(transactions: list[dict]) -> dict:
    """Bulk import transactions to YNAB. Returns {imported, duplicates}."""
    config = BanecoConfig()
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.import_transactions(transactions)


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
