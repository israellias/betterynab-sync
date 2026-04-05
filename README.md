# betterynab-sync

Multi-currency budget synchronization for [YNAB](https://www.ynab.com/). Automates bank transaction imports and syncs across currency budgets so you can track real costs from a single place.

## The problem

You earn in one currency but spend in others. YNAB doesn't natively handle multi-currency budgets, so you end up with separate budgets per currency and no unified view of your spending. Exchange rate volatility makes it worse: you can't tell how much (in your main currency) you actually spent last week.

This project solves it in two steps:

1. **Automate bank imports**: each bank/exchange gets a pipeline that exports transactions and bulk-imports them into YNAB with deduplication. Reusable and easy to extend to new banks.

2. **Sync across currencies**: transactions from secondary budgets (e.g. BOB, ARS) get mirrored into a main budget (e.g. USD) with exchange rate conversion. This part currently has hardcoded budget names and account IDs, it works but isn't yet generic.

## Setup

### Prerequisites

- Python 3.11+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (for AI-powered sync skills)

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Configuration

```bash
cp .env.example .env
```

Fill in your YNAB token, account IDs, and bank credentials for the pipelines you use. See `.env.example` for all available variables grouped by pipeline.

## Part 1: Bank pipelines (reusable)

Each bank integration follows the same 4-step pattern: **export** from the bank, **convert** to YNAB format, optionally **categorize** with AI, and **import** to YNAB.

### Pipeline architecture

```
bank_module/
  config.py      # Reads env vars for this bank's credentials + YNAB target
  exporter.py    # Playwright-based login + transaction download
  converter.py   # Bank-specific format -> YNAB transaction dicts
  pipeline.py    # Orchestrates: export -> convert -> import
  __init__.py    # Public API: load_pending_transactions(), import_to_ynab(), etc.
  __main__.py    # CLI entry point: python -m <module>
```

### Shared services

- **`services/ynab_importer.py`**: `YNABImporter(budget_name, account_id)` handles bulk upload to YNAB with `import_id` deduplication (safe to re-run)
- **`services/_ynab_connection/`**: YNAB API client

### Running a pipeline

All pipelines share the same CLI interface:

```bash
python -m <module>                          # Full pipeline (auto-detects last sync date)
python -m <module> --since-date 2026-02-01  # Override start date
python -m <module> --export-only            # Just download, no YNAB upload
python -m <module> --dry-run                # Export + convert, save to <module>/transactions.json
python -m <module> --reset                  # Clear browser state and re-login
```

### AI-powered categorization

The `/sync-baneco` and `/sync-bisa` Claude Code skills wrap the pipeline with AI-powered payee and category assignment. They use `rules.md` files (auto-created on first run) for deterministic matching, with AI judgment for unmatched transactions.


### Current integrations

| Module | Bank | Country | Export method |
| --- | --- | --- | --- |
| `baneco/` | Banco Economico | Bolivia | Playwright + CSV download |
| `bisa/` | Banco BISA | Bolivia | Playwright + CSV download |
| `binance/` | Binance P2P | Global | Playwright + API intercept |

### Weekly reconciliation

The `/reconcile` skill runs all 3 pipelines, then compares bank balances against YNAB account balances and prints a discrepancy report. It never makes changes automatically.

### Adding a new bank

1. Create a new directory (e.g. `bancosol/`)
2. Implement the 4 files following the pattern above:
   - `config.py`: follow the `BanecoConfig` pattern, read env vars with a `BANCOSOL_` prefix
   - `exporter.py`: Playwright-based export (or any method that produces a file)
   - `converter.py`: parse the bank's export format into YNAB transaction dicts with `import_id` for dedup
   - `pipeline.py`: wire together exporter, converter, and `YNABImporter`
3. Add `__main__.py` for CLI usage and `__init__.py` with public API
4. Add env vars to `.env.example`
5. Optionally, add a Claude Code skill in `.claude/skills/sync-<bank>/` for AI categorization

The `import_id` field in each transaction must be unique and deterministic (e.g. `PREFIX:txn_id:date`) so re-runs skip already-imported transactions.

## Part 2: Cross-currency sync (work in progress)

Once transactions are in YNAB, the second step is syncing them from secondary budgets into a main budget with exchange rate conversion. This lets you see all spending in one currency.

### Daily sync

`main.py` reads transactions from secondary budgets and creates corresponding entries in the main budget, converting amounts using the most recent exchange rate (`[TC:rate]` in memos).

```bash
python main.py --since-date YYYY-MM-DD

# Sync only BISA credit card transactions (for late statements)
python main.py --since-date YYYY-MM-DD --credit-card
```

### Automated sync

The `/sync-bob` Claude Code skill automates the full cycle: resolves the since-date from the last reconciled transaction, seeds the exchange rate, runs the sync, and prints a balance comparison.

> **Note**: this part currently has hardcoded budget names ("USD Budget", "BOB Budget", "ARS Budget"), a hardcoded BISA CC account ID, and Bolivia-specific logic in `services/budget_provider.py` and `services/transaction_provider.py`. It works for the original setup but isn't yet configurable for other currency pairs. Contributions to make this generic are welcome.

### Other utilities

- **`file_import/`**: standalone scripts that convert bank statements (CSV, PDF, JSON, XLSX) to YNAB-compatible CSV for manual import

## Scheduled automation (macOS)

The Baneco sync can run daily via a macOS launchd agent. See `config/com.betterynab.sync-baneco.plist` for the template.

```bash
cp config/com.betterynab.sync-baneco.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.betterynab.sync-baneco.plist
```

Requires an active macOS session (Playwright opens a visible browser), Claude Code installed and authenticated, and Node.js in PATH.

### Managing the agent

```bash
# Test run immediately
launchctl start com.betterynab.sync-baneco

# Check logs
cat /tmp/sync-baneco.log    # stdout (Claude output)
cat /tmp/sync-baneco.err    # stderr (errors)

# Stop the schedule
launchctl unload ~/Library/LaunchAgents/com.betterynab.sync-baneco.plist
```

### Requirements

- macOS user session must be active (logged in) — Playwright opens a visible browser
- Claude Code must be installed and authenticated
- Node.js must be available in PATH (the plist includes `/opt/homebrew/bin`)

### Plist reference

The plist is stored in `config/com.betterynab.sync-baneco.plist`. It runs daily at 11:30 AM (local time) and uses `--auto-accept` to skip the review table and `--allowedTools` to grant the necessary permissions for non-interactive execution.
