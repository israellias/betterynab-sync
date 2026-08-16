"""Dump the BOB Budget ledger and its mirror account in USD Budget. Read-only.

The bare /transactions endpoint silently trims to roughly the last year, which makes
every balance derived from it wrong. Always pass an explicit since_date.
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.youneedabudget.com/v1"
EPOCH = "1990-01-01"
OUT = os.environ.get("AUDIT_DIR", ".audit")
headers = {"Authorization": f"Bearer {os.environ['YNAB_TOKEN']}"}


def get(path, **params):
    response = requests.get(f"{API}{path}", headers=headers, params=params)
    response.raise_for_status()
    return response.json()["data"]


budgets = {b["name"]: b["id"] for b in get("/budgets")["budgets"]}
bob_budget_id = budgets["BOB Budget"]
usd_budget_id = budgets["USD Budget"]
bob_account_in_usd = os.environ["BOB_BUDGET_ACCOUNT"]

payload = {
    "bob_budget_id": bob_budget_id,
    "usd_budget_id": usd_budget_id,
    "bob_account_in_usd": bob_account_in_usd,
    "bob_accounts": get(f"/budgets/{bob_budget_id}/accounts")["accounts"],
    "usd_accounts": get(f"/budgets/{usd_budget_id}/accounts")["accounts"],
    "bob_transactions": get(f"/budgets/{bob_budget_id}/transactions", since_date=EPOCH)["transactions"],
    "usd_bob_account_transactions": get(
        f"/budgets/{usd_budget_id}/accounts/{bob_account_in_usd}/transactions", since_date=EPOCH
    )["transactions"],
}

os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/ledgers.json", "w") as f:
    json.dump(payload, f, ensure_ascii=False)

print(f"saved {OUT}/ledgers.json")
print(f"  BOB transactions           : {len(payload['bob_transactions'])}")
print(f"  USD/BOB-account transactions: {len(payload['usd_bob_account_transactions'])}")

# A mismatch here means the dump is incomplete and nothing downstream can be trusted.
for account in payload["bob_accounts"]:
    if account["closed"] or account["deleted"]:
        continue
    ledger = sum(
        t["amount"] / 1000.0
        for t in payload["bob_transactions"]
        if not t["deleted"] and t["account_id"] == account["id"]
    )
    balance = account["balance"] / 1000.0
    flag = "" if abs(ledger - balance) < 0.005 else "   <-- INCOMPLETE DUMP"
    print(f"  {account['name']:<14} ledger {ledger:>12,.2f} | balance {balance:>12,.2f}{flag}")
