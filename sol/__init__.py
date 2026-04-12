import json
import os

from sol.config import SolConfig
from sol.converter import SolConverter
from sol.exporter import SolExporter
from sol.pipeline import SolPipeline
from services.ynab_importer import YNABImporter

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSACTIONS_PATH = os.path.join(MODULE_DIR, "transactions.json")
EXPORT_PATH = os.path.join(MODULE_DIR, "export.pdf")

__all__ = [
    "SolConfig",
    "SolConverter",
    "SolExporter",
    "SolPipeline",
    "load_pending_transactions",
    "import_to_ynab",
    "get_bob_categories",
    "get_last_balance",
    "get_ynab_balance",
]


def load_pending_transactions() -> list[dict]:
    """Load transactions from sol/transactions.json."""
    if not os.path.exists(TRANSACTIONS_PATH):
        raise FileNotFoundError(f"No pending transactions file found at {TRANSACTIONS_PATH}")
    with open(TRANSACTIONS_PATH, "r") as f:
        return json.load(f)


def import_to_ynab(transactions: list[dict]) -> dict:
    """Bulk import transactions to YNAB. Returns {imported, duplicates}."""
    config = SolConfig()
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.import_transactions(transactions)


def get_last_balance() -> float:
    """Read the last 'Saldo' value from sol/export.pdf.

    Parses the PDF and returns the balance from the first transaction
    (most recent, as transactions are in reverse chronological order).
    """
    import PyPDF2
    import re

    if not os.path.exists(EXPORT_PATH):
        raise FileNotFoundError(f"No export file found at {EXPORT_PATH}")

    with open(EXPORT_PATH, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

    # Find all "Bs X,XXX.XX" balance values (the Saldo column)
    # Pattern: after an amount like "+Bs X.XX" or "-Bs X.XX", the next "Bs X.XX" is the balance
    balance_pattern = re.compile(r'[+-]Bs\s*[\d,]+\.?\d*\s+Bs\s*([\d,]+\.?\d*)')
    matches = balance_pattern.findall(full_text)

    if not matches:
        raise ValueError("No balance found in export PDF.")

    # First match is the most recent transaction's balance
    return float(matches[0].replace(",", ""))


def get_bob_categories() -> list[dict]:
    """Fetch active categories from BOB Budget via YNAB API.

    Returns list of {"id": ..., "name": ...} dicts.
    """
    from dotenv import load_dotenv
    from services._ynab_connection import YNABClient

    load_dotenv()
    config = SolConfig()
    client = YNABClient()
    budgets = client.get_budgets()
    bob = next((b for b in budgets if b.name == config.ynab_budget_name), None)
    if not bob:
        raise ValueError(f"Budget '{config.ynab_budget_name}' not found in YNAB.")
    categories = client.get_categories(bob.id)
    return [{"id": c.id, "name": c.name} for c in categories if not c.hidden and not c.deleted]


def get_ynab_balance() -> dict:
    """Get YNAB balance for this module's account.

    Returns dict with balance, cleared_balance, uncleared_balance (milliunit x 1000).
    """
    from dotenv import load_dotenv

    load_dotenv()
    config = SolConfig()
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.get_account_balance()
