---
name: sync-bob
description: Sync BOB Budget transactions to USD Budget with exchange rate conversion
argument-hint: ""
allowed-tools: Bash(.venv/bin/python:*)
---

# Sync BOB Budget → USD Budget

All python commands MUST use `.venv/bin/python` (not `python` or `python3`).

This skill prepares preconditions and runs `main.py` to sync BOB Budget transactions
to the USD Budget with exchange rate conversion.

## Phase 1 — Resolve since-date

Find the latest **reconciled** transaction in USD Budget → BOB Budget Account.
That date becomes `--since-date` for the sync.

Run:
```bash
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import os, json
from services._ynab_connection import YNABClient
client = YNABClient()
budgets = client.get_budgets()
usd = next(b for b in budgets if b.name == 'USD Budget')
txns = client.get_transactions(usd.id)
bob_acct = os.environ['BOB_BUDGET_ACCOUNT']
reconciled = [t for t in txns if t.account_id == bob_acct and t.cleared == 'reconciled']
reconciled.sort(key=lambda t: t.date, reverse=True)
latest = reconciled[0] if reconciled else None
print(json.dumps({
    'date': latest.date if latest else None,
    'memo': latest.memo if latest else None,
    'exchange_rate': latest.exchange_rate if latest else None,
}))
"
```

Save the `date` as `{since_date}`. Print it to the user:
> Since-date resolved: **{since_date}** (from last reconciled transaction)

If `date` is null, ask the user to provide a `--since-date` manually.

## Phase 2 — Find latest TC rate & create seed transaction

The sync script uses `[TC:rate]` memos to determine the exchange rate. Without one in
the date range, it defaults to 1.0 which would produce wrong amounts.

Find the latest **reconciled** TC rate and create a seed transaction:

```bash
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import os, json
from services._ynab_connection import YNABClient
client = YNABClient()
budgets = client.get_budgets()
usd = next(b for b in budgets if b.name == 'USD Budget')
bob_acct = os.environ['BOB_BUDGET_ACCOUNT']
txns = client.get_transactions(usd.id)
with_tc = [t for t in txns if t.account_id == bob_acct and t.exchange_rate is not None and t.cleared == 'reconciled']
with_tc.sort(key=lambda t: t.date, reverse=True)
rate = with_tc[0].exchange_rate
client.create_transaction(usd.id, {
    'account_id': bob_acct, 'date': '{since_date}', 'amount': 10,
    'payee_name': None, 'category_id': None,
    'memo': f'[TC:{rate}] FX rate seed',
    'cleared': 'cleared', 'approved': True, 'flag_color': None,
})
print(json.dumps({'rate': rate}))
"
```

Note: replace `{since_date}` in the script above with the actual date from Phase 1.

Print to the user:
> Seed transaction created: **[TC:{rate}]** on {since_date} (0.01 USD)

Save `{rate}` for Phase 4.

## Phase 3 — Run the sync

Run main.py with the resolved since-date:

```bash
.venv/bin/python main.py --since-date {since_date}
```

Capture and show the output to the user. Each line like
`Created transaction {id}` means a BOB transaction was synced to USD.

## Phase 4 — Balance comparison

Get BOB Budget total and BOB Account balance in USD Budget:

```bash
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import os, json
from services._ynab_connection import YNABClient
client = YNABClient()
budgets = client.get_budgets()
bob = next(b for b in budgets if b.name == 'BOB Budget')
bob_accounts = client.get_accounts(bob.id)
bob_total = sum(a['balance'] for a in bob_accounts if not a['closed'] and not a['deleted'])
usd = next(b for b in budgets if b.name == 'USD Budget')
usd_accounts = client.get_accounts(usd.id)
bob_acct_id = os.environ['BOB_BUDGET_ACCOUNT']
bob_in_usd = next(a for a in usd_accounts if a['id'] == bob_acct_id)
print(json.dumps({
    'bob_total_milliunits': bob_total,
    'bob_in_usd_milliunits': bob_in_usd['balance'],
}))
"
```

Compute and print:
- `bob_total` = `bob_total_milliunits / 1000.0`
- `bob_in_usd` = `bob_in_usd_milliunits / 1000.0`
- `bob_converted` = `bob_total / {rate}` (using TC rate from Phase 2)
- `diff` = `bob_converted - bob_in_usd`

```
## BOB → USD Sync Summary

| Metric | Value |
|--------|-------|
| BOB Budget total | {bob_total} Bs |
| Latest TC rate | {rate} |
| BOB total in USD (BOB / TC) | {bob_converted} USD |
| BOB Account in USD Budget | {bob_in_usd} USD |
| Difference | {diff} USD |

### Analysis
```

Analysis rules:
- **diff within +/- 5 USD**: "Normal exchange rate rounding across multiple transactions."
- **diff > 5 USD**: List possible causes:
  - Transactions in BOB Budget not yet synced (check if any were skipped)
  - Categories with gear emoji excluded from sync
  - Transfer transactions excluded from sync
  - Manual adjustments in either budget
  - Exchange rate changed between transactions

**NEVER make changes automatically** to fix discrepancies. Only report them.
