import os
import sys


class SolConfig:
    REQUIRED_VARS = {
        "SOL_USERNAME": "username",
        "SOL_PASSWORD": "password",
        "SOL_YNAB_BUDGET": "ynab_budget_name",
        "SOL_YNAB_ACCOUNT": "ynab_account_id",
    }

    def __init__(self):
        missing = [var for var in self.REQUIRED_VARS if not os.environ.get(var)]
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}", flush=True)
            print("Copy .env.example to .env and fill in your values.", flush=True)
            sys.exit(1)

    @property
    def username(self) -> str:
        return os.environ["SOL_USERNAME"]

    @property
    def password(self) -> str:
        return os.environ["SOL_PASSWORD"]

    @property
    def ynab_budget_name(self) -> str:
        return os.environ["SOL_YNAB_BUDGET"]

    @property
    def ynab_account_id(self) -> str:
        return os.environ["SOL_YNAB_ACCOUNT"]
