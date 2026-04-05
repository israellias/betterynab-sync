import os
import sys


class BinanceConfig:
    REQUIRED_VARS = {
        "BINANCE_YNAB_BUDGET": "ynab_budget_name",
        "BINANCE_YNAB_ACCOUNT": "ynab_account_id",
        "BINANCE_TRANSFER_PAYEE": "transfer_payee_id",
    }

    def __init__(self):
        missing = [var for var in self.REQUIRED_VARS if not os.environ.get(var)]
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}", flush=True)
            print("Copy .env.example to .env and fill in your values.", flush=True)
            sys.exit(1)

    @property
    def ynab_budget_name(self) -> str:
        return os.environ["BINANCE_YNAB_BUDGET"]

    @property
    def ynab_account_id(self) -> str:
        return os.environ["BINANCE_YNAB_ACCOUNT"]

    @property
    def transfer_payee_id(self) -> str:
        return os.environ["BINANCE_TRANSFER_PAYEE"]
