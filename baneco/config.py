import os
import sys


class BanecoConfig:
    REQUIRED_VARS = {
        "BANECO_ACCOUNT": "baneco_account",
        "BANECO_USERNAME": "baneco_username",
        "BANECO_PASSWORD": "baneco_password",
        "BANECO_YNAB_BUDGET": "ynab_budget_name",
        "BANECO_YNAB_ACCOUNT": "ynab_account_id",
    }

    def __init__(self):
        missing = [var for var in self.REQUIRED_VARS if not os.environ.get(var)]
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}", flush=True)
            print("Copy .env.example to .env and fill in your values.", flush=True)
            sys.exit(1)

    @property
    def baneco_account(self) -> str:
        return os.environ["BANECO_ACCOUNT"]

    @property
    def baneco_username(self) -> str:
        return os.environ["BANECO_USERNAME"]

    @property
    def baneco_password(self) -> str:
        return os.environ["BANECO_PASSWORD"]

    @property
    def ynab_budget_name(self) -> str:
        return os.environ["BANECO_YNAB_BUDGET"]

    @property
    def ynab_account_id(self) -> str:
        return os.environ["BANECO_YNAB_ACCOUNT"]
