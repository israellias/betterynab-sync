# betterynab-sync

## Main Goal

When you get your main income in a single currency and/or you intent to use a single currency to leave money there. But you are spending money in different currencies then you get trouble syncing this expenses in both currencies.

The problem increases its complexity when volatity on exchange rates is present. That leads you to not know how many (in local) money could you expend e.g. the last week of the month.

So the main goal is to handle budgets that occur in different currencies but, at the same time, get their incomes from the same source (This is the main budget)

# Explanation

You could use your **main budget** for:

- Assign money for all your categories (even those that has their transactions in other currency).

You could use your **second budgets** for:

- Register money in your local currency and this will create a transaction in your main budget applying the current exchange rate. Which indicates the real cost of everything you're expending.

Finally you could pay attention on a single budget (the main one) and start increasing the Age of Money and see relevant reports on how much you're expending and in what.

## Setup

### Prerequisites

- Python 3.11+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Node.js (required by Claude Code)

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # one-time: downloads browser for Baneco export
```

### Configuration

**Environment variables** in `.env`:

| Variable | Description |
|---|---|
| `YNAB_TOKEN` | YNAB API token |
| `BOB_BUDGET_ACCOUNT` | Account ID in USD Budget for BOB transactions |
| `ARS_BUDGET_ACCOUNT` | Account ID in USD Budget for ARS transactions |

**Baneco credentials** in `baneco_config.json` (copy `baneco_config.example.json` to get started). Each teammate can have their own config since this file is gitignored.

**Baneco transaction rules** in `baneco/rules.md`. This markdown file contains payee patterns, category mappings, and AI guidance used by the `/sync-baneco` skill to categorize transactions. Edit the tables directly to add or change rules.

## How to use

### Daily sync

Run the sync script to pull transactions from secondary budgets into the main budget:

```bash
python main.py --since-date YYYY-MM-DD
```

For BISA credit card late statements only:

```bash
python main.py --since-date YYYY-MM-DD --credit-card
```

### Baneco pipeline

Full pipeline: exports transactions from benet.baneco.com.bo via Playwright, converts them, and bulk imports to YNAB with automatic deduplication.

```bash
python -m baneco                          # Full pipeline (auto-detects last sync date)
python -m baneco --since-date 2026-02-01  # Override start date
python -m baneco --export-only            # Just download CSV, no YNAB upload
python -m baneco --dry-run                # Export + convert, save to baneco/transactions.json
python -m baneco --reset                  # Clear browser state and re-login
```

On first run it requires a 2FA code; subsequent runs skip 2FA because the browser state is preserved. When 2FA is required, write the code to:

```bash
echo "123456" > /tmp/baneco_2fa_code
```

### AI-powered sync (recommended)

The `/sync-baneco` skill runs the full Baneco pipeline with AI-powered payee and category assignment. In Claude Code:

```
/sync-baneco
/sync-baneco --since-date 2026-02-01
```

It exports from the bank, applies deterministic rules from `baneco/rules.md`, uses AI judgment for unmatched transactions, shows a review table, and imports to YNAB on approval.

### File import converters

These scripts convert bank/exchange statements into YNAB-compatible CSV (`ynab.csv`):

| Script | Source | Format |
|---|---|---|
| `file_import/baneco.py` | Baneco bank statement | CSV |
| `file_import/bisaccpdf.py` | BISA credit card statement | PDF |
| `file_import/bisa.py` | BISA debit statement | CSV |
| `file_import/binance.py` | Binance P2P trades | JSON |
| `file_import/gananet.py` | Gananet statement | XLSX |
| `file_import/mp.py` | Mercado Pago transactions | JSON |

```bash
python file_import/<script> <file>
```

### Preconditions

1. Your categories (of the main budget) needs to be present in all the other budgets (have the same name)
1. Transactions of a category that has "⚙️" will be ignored
1. You must have an **account** in the main budget that have the same name that your secondary budget has. That means, one account per each secondary budget

### Restrictions

Budget names are currently hardcoded:

- **USD Budget** (main budget)
- **BOB Budget**
- **ARS Budget**

## Scheduled automation (macOS)

The Baneco sync can run daily via a macOS launchd agent that triggers Claude Code in non-interactive mode.

### Setup

1. Copy the plist to your LaunchAgents directory:

```bash
cp config/com.betterynab.sync-baneco.plist ~/Library/LaunchAgents/
```

2. Edit the plist to match your paths if needed (working directory, claude binary location).

3. Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.betterynab.sync-baneco.plist
```

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
