---
name: sync-bisa
description: Export BISA transactions, categorize with AI, and import to YNAB
argument-hint: "[--auto-accept] [--since-date YYYY-MM-DD]"
allowed-tools: Bash(.venv/bin/python:*), Read, Write
model: sonnet
---

# Sync BISA Pipeline

All python commands MUST use `.venv/bin/python` (not `python` or `python3`).

When the user runs this skill:

1. Run the export + convert pipeline:
   `.venv/bin/python -m bisa --dry-run [--since-date YYYY-MM-DD if provided]`
   (This opens the browser, exports CSV, converts transactions, saves to bisa/transactions.json)

2. Load the converted transactions:
   `.venv/bin/python -c "import json; from bisa import load_pending_transactions; print(json.dumps(load_pending_transactions()))"`

3. Check if `bisa/rules.md` exists:
   - **If it exists**: read it for deterministic rules
   - **If it doesn't exist**: ask the user to provide their transaction categorization rules, explaining the expected structure:
     - **Credit Card Payment Rules**: list of memo patterns that indicate a credit card payment (these get assigned to a transfer account)
     - **Amount-Based Rules**: a markdown table with columns `Pattern (in memo) | Amount Range | Payee | Category` for when transaction amounts determine categorization (e.g. loan payments by amount range)
     - **AI Guidance**: free-form notes to help categorize unmatched transactions (e.g. "POS transactions are usually stores", "TRASP.CTAS.TERCEROS are bank transfers")
     Write the user's input to `bisa/rules.md` with proper markdown formatting, then continue

4. Fetch BOB Budget categories (returns `[{"id": "uuid", "name": "Category Name"}, ...]`):
   `.venv/bin/python -c "import json; from bisa import get_bob_categories; print(json.dumps(get_bob_categories()))"`

5. For each transaction:
   a. Apply payee+category rules from bisa/rules.md (pattern matching on memo)
   b. Apply amount-based rules (e.g. SYSPago ranges)
   c. For unmatched: use AI judgment based on memo text + AI Guidance section in bisa/rules.md
   d. Fuzzy-match the rule's category name against actual YNAB category names (ignore emojis)
   e. Set `category_id` on the transaction using the matched category's `id` (YNAB requires the UUID, not a name)

6. If --auto-accept was passed: skip to step 8

7. Show the user a table:
   `Date | Amount | Payee | Category | Memo (truncated) | Source (rule/AI)`
   Ask user to approve or adjust

8. Write the final categorized transactions back to `bisa/transactions.json`, then import to YNAB:
   `.venv/bin/python -c "import json, sys; from bisa import import_to_ynab; txns = json.loads(sys.stdin.read()); result = import_to_ynab(txns); print(json.dumps(result))"` (pipe the JSON via stdin)
