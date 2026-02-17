import json
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_DIR, "baneco_config.json")


class BanecoConfig:
    REQUIRED_KEYS = [
        "baneco_account",
        "baneco_username",
        "baneco_password",
        "ynab_budget_name",
        "ynab_account_id",
    ]

    def __init__(self, path=None):
        self._path = path or DEFAULT_CONFIG_PATH
        self._data = self._load()

    def _load(self):
        if not os.path.exists(self._path):
            print(f"Config not found: {self._path}", flush=True)
            print(
                "Copy baneco_config.example.json and fill in your values.", flush=True
            )
            sys.exit(1)

        with open(self._path) as f:
            data = json.load(f)

        missing = [k for k in self.REQUIRED_KEYS if k not in data]
        if missing:
            print(f"Missing config keys: {', '.join(missing)}", flush=True)
            sys.exit(1)

        return data

    @property
    def baneco_account(self) -> str:
        return self._data["baneco_account"]

    @property
    def baneco_username(self) -> str:
        return self._data["baneco_username"]

    @property
    def baneco_password(self) -> str:
        return self._data["baneco_password"]

    @property
    def ynab_budget_name(self) -> str:
        return self._data["ynab_budget_name"]

    @property
    def ynab_account_id(self) -> str:
        return self._data["ynab_account_id"]
