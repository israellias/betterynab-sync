import json
import os

from binance.config import BinanceConfig
from binance.converter import BinanceConverter
from binance.exporter import BinanceExporter
from binance.pipeline import BinancePipeline

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
BALANCE_PATH = os.path.join(MODULE_DIR, "balance.json")

__all__ = [
    "BinanceConfig",
    "BinanceConverter",
    "BinanceExporter",
    "BinancePipeline",
    "get_usdt_balance",
    "get_ynab_balance",
]


def get_usdt_balance() -> float | None:
    """Read USDT balance from binance/balance.json if available."""
    if not os.path.exists(BALANCE_PATH):
        return None
    with open(BALANCE_PATH, "r") as f:
        data = json.load(f)
    return data.get("usdt_balance")


def get_ynab_balance() -> dict:
    """Get YNAB balance for this module's account.

    Returns dict with balance, cleared_balance, uncleared_balance (milliunit × 1000).
    """
    from dotenv import load_dotenv
    from services.ynab_importer import YNABImporter

    load_dotenv()
    config = BinanceConfig()
    importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)
    return importer.get_account_balance()
