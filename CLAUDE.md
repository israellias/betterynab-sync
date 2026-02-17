# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

betterynab-sync is a multi-currency budget synchronization tool for YNAB (You Need A Budget). It syncs transactions from secondary budgets (BOB Budget, ARS Budget) to a main budget (USD Budget), applying exchange rates to track real costs across currencies.

### Core Concept

- **Main Budget**: USD Budget - where all money is assigned and tracked
- **Secondary Budgets**: BOB Budget, ARS Budget - where local currency transactions are recorded
- Each secondary budget has a corresponding account in the main budget
- Transactions sync daily with exchange rate conversion using `[TC:rate]` format in memos
- Transaction identifiers use format `{transaction_id[:8]}|{MMDD}` to prevent duplicates

## Commands

### Running the sync
```bash
# Sync transactions from a specific date (required)
python main.py --since-date YYYY-MM-DD

# Sync only BISA credit card transactions (for late statements)
python main.py --since-date YYYY-MM-DD --credit-card
```

### Baneco full pipeline
```bash
# Export from bank + convert + bulk import to YNAB (auto since-date)
python -m baneco

# Override start date
python -m baneco --since-date YYYY-MM-DD

# Export only (no YNAB upload)
python -m baneco --export-only

# Dry run: export + convert, save to baneco_transactions.json (no YNAB upload)
python -m baneco --dry-run

# Reset browser state
python -m baneco --reset
```

Configuration in `baneco_config.json` (gitignored, see `baneco_config.example.json`).
Payee/category rules in `baneco_rules.md` (human-editable markdown tables).
Uses YNAB bulk import with `import_id` dedup — safe to re-run.

### File Import Scripts
These standalone scripts convert bank/exchange statements to YNAB CSV format. All output to `ynab.csv`:

```bash
# BISA Credit Card PDF import (credit card statements)
python file_import/bisaccpdf.py <pdf_file>

# Binance P2P trades (JSON export)
python file_import/binance.py <json_file>

# Gananet Excel statements
python file_import/gananet.py <xlsx_file>

# Other bank imports (BISA debit, Mercado Pago, etc.)
python file_import/bisa.py <csv_file>
python file_import/mp.py <json_file>
python file_import/baneco.py <csv_file>
```

## Environment Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium  # one-time: downloads Chromium for Baneco export
```

Required environment variables in `.env`:
- `YNAB_TOKEN` - YNAB API token
- `BOB_BUDGET_ACCOUNT` - Account ID in USD Budget for BOB transactions
- `ARS_BUDGET_ACCOUNT` - Account ID in USD Budget for ARS transactions

## Architecture

### Directory Structure

- `baneco/` - Baneco bank pipeline (export → convert → YNAB import)
  - `config.py` - `BanecoConfig` — loads baneco_config.json
  - `exporter.py` - `BanecoExporter` — Playwright login + CSV download
  - `converter.py` - `BanecoConverter` — Baneco CSV → YNAB transactions
  - `importer.py` - `YNABImporter` — bulk upload via YNAB API
  - `pipeline.py` - `BanecoPipeline` — orchestrates the 4 steps
- `models/` - Data models (Budget, Transaction, Category)
- `services/` - Business logic and API integration
  - `_ynab_connection/` - YNAB API client and transaction interface
  - `budget_provider.py` - Budget and category fetching/validation
  - `transaction_provider.py` - Transaction processing and sync logic
- `tasks/` - High-level sync operations
  - `sync_transactions.py` - Main transaction sync orchestration
  - `sync_categories.py` - Category synchronization (currently disabled)
- `file_import/` - Bank/exchange statement converters (CSV/PDF/JSON → YNAB CSV)

### Transaction Sync Flow

1. `sync_transactions()` fetches main + secondary budgets via `relevant_budgets()`
2. Fetches transactions from `since_date` for all budgets via `fill_transactions()`
3. For each secondary budget, calls `sync_transactions_to_main_budget()`:
   - Filters transactions based on credit card mode flag
   - Excludes transfers, categories with ⚙️ emoji, and duplicates
   - Converts amounts using exchange rate from most recent transaction
   - Creates transactions in main budget via YNAB API

### Key Business Rules

- Categories with "⚙️" emoji are ignored during sync
- Budget names are hardcoded: "USD Budget", "BOB Budget", "ARS Budget"
- BISA CC account (`2096c0e6-e608-4373-8346-4414ee53664c`) can be synced separately
- Exchange rates stored in transaction memos as `[TC:rate]`
- Transaction matching uses identifier comparison to prevent duplicates
- Subtransactions are processed individually when present

### Exchange Rate Handling

- Exchange rates extracted from memo field using pattern `[TC:(\d+(?:\.\d+)?)]`
- For each new transaction, uses most recent exchange rate from same account
- Amount conversion: `int(local_amount / exchange_rate)` (YNAB stores amounts × 1000)
- Falls back to 1.0 if no previous exchange rate found

### BISA Credit Card Workflow

BISA CC transactions exist in two modes:
- **Default mode** (`--credit-card` not set): Excludes BISA CC (imported directly to USD)
- **Credit card mode** (`--credit-card` set): Syncs ONLY BISA CC for late statements

Import workflow:
1. Extract PDF: `python file_import/bisaccpdf.py statement.pdf`
2. Import `ynab.csv` to BISA CC account in BOB Budget
3. Sync to USD Budget: `python main.py --since-date YYYY-MM-DD --credit-card`

