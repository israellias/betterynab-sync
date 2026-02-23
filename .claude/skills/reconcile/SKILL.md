---
name: reconcile
description: Sync all bank pipelines and reconcile balances against YNAB
argument-hint: ""
allowed-tools: Bash(.venv/bin/python:*), Read, Write, Skill(sync-baneco:*), Skill(sync-bisa:*)
---

# Weekly Reconciliation

All python commands MUST use `.venv/bin/python` (not `python` or `python3`).

When the user runs this skill:

## Phase 1 — Sync all pipelines

Run all 3 pipelines sequentially. Track the import results (imported/duplicates) for each.

1. Invoke `/sync-baneco --auto-accept` — note the imported/duplicates counts from the output
2. Invoke `/sync-bisa --auto-accept` — note the imported/duplicates counts from the output
3. Run Binance pipeline directly (no AI categorization needed):
   `.venv/bin/python -m binance`
   Parse the "Imported X transactions (Y duplicates skipped)" line from output.

## Phase 2 — Collect balances

4. Get bank/exchange balances from exported data:
   - Baneco: `.venv/bin/python -c "from baneco import get_last_balance; print(get_last_balance())"`
   - BISA: `.venv/bin/python -c "from bisa import get_last_balance; print(get_last_balance())"`
   - Binance: `.venv/bin/python -c "from binance import get_usdt_balance; print(get_usdt_balance())"`

5. Get YNAB account balances:
   - Baneco: `.venv/bin/python -c "import json; from baneco import get_ynab_balance; print(json.dumps(get_ynab_balance()))"`
   - BISA: `.venv/bin/python -c "import json; from bisa import get_ynab_balance; print(json.dumps(get_ynab_balance()))"`
   - Binance: `.venv/bin/python -c "import json; from binance import get_ynab_balance; print(json.dumps(get_ynab_balance()))"`

   YNAB balances are in milliunit format (× 1000). Divide by 1000.0 to get the human-readable amount.

## Phase 3 — Reconciliation report

6. Print a summary using this format:

```
## Weekly Reconciliation — {today's date}

### Sync Results
| Pipeline | Imported | Duplicates |
|----------|----------|------------|
| Baneco   | {n}      | {n}        |
| BISA     | {n}      | {n}        |
| Binance  | {n}      | {n}        |

### Balance Comparison (BOB Budget)
| Account  | Bank Balance | YNAB Balance | Diff    | Status |
|----------|-------------|--------------|---------|--------|
| Baneco   | {x} Bs      | {y} Bs       | {diff}  | {ok}   |
| BISA     | {x} Bs      | {y} Bs       | {diff}  | {ok}   |

### Balance Comparison (USD Budget)
| Account  | Exchange      | YNAB Balance | Diff    | Status |
|----------|--------------|--------------|---------|--------|
| Binance  | {x} USDT     | {y} USD      | {diff}  | {ok}   |
```

Status column rules:
- Diff == 0 (or within 0.01): show checkmark
- Diff != 0: show warning sign

7. If there are discrepancies, add a "### Discrepancy Analysis" section listing possible causes:
   - Recent transaction not yet synced
   - Rounding difference in conversion
   - Pending/uncleared transactions
   - Manual adjustment needed

8. **NEVER make changes automatically** to fix discrepancies. Only report them.

Notes:
- If Binance balance is None (balance.json not found), note it as "N/A" in the table
- If any pipeline fails, still continue with the others and note the failure
- Bank balances from CSVs reflect the balance at the time of the last transaction in the export
