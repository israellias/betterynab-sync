---
name: sync-baneco
description: Export Baneco transactions, categorize with AI, and import to YNAB
argument-hint: "[--auto-accept] [--since-date YYYY-MM-DD]"
allowed-tools: Bash(.venv/bin/python:*), Read, Write
model: sonnet
---

# Sync Baneco Pipeline

All python commands MUST use `.venv/bin/python` (not `python` or `python3`).

When the user runs this skill:

1. Run the export + convert pipeline:
   `.venv/bin/python -m baneco --dry-run [--since-date YYYY-MM-DD if provided]`
   (This opens the browser, exports CSV, converts transactions, saves to baneco/transactions.json)

2. Load the converted transactions:
   `.venv/bin/python -c "import json; from baneco import load_pending_transactions; print(json.dumps(load_pending_transactions()))"`

3. Check if `baneco/rules.md` exists:
   - **If it exists**: read it for deterministic rules
   - **If it doesn't exist**: ask the user to provide their transaction categorization rules, explaining the expected structure:
     - **Payee + Category Rules**: a markdown table with columns `Pattern (in memo) | Payee | Category` for when a memo pattern should set both payee and category
     - **Category-Only Rules**: a markdown table with columns `Keywords | Category` for keyword-based category matching where AI determines the payee
     - **AI Guidance**: free-form notes to help categorize unmatched transactions (e.g. "POS transactions are usually stores", "TRASP.CTAS.TERCEROS are bank transfers")
     Write the user's input to `baneco/rules.md` with proper markdown formatting, then continue

4. Fetch BOB Budget categories (returns `[{"id": "uuid", "name": "Category Name"}, ...]`):
   `.venv/bin/python -c "import json; from baneco import get_bob_categories; print(json.dumps(get_bob_categories()))"`

5. For each transaction:
   a. Apply payee+category rules from baneco/rules.md (pattern matching on memo)
   b. Apply category-only rules (keyword matching on memo)
   c. For unmatched: use AI judgment based on memo text + AI Guidance section in baneco/rules.md
   d. Fuzzy-match the rule's category name against actual YNAB category names (ignore emojis)
   e. Set `category_id` on the transaction using the matched category's `id` (YNAB requires the UUID, not a name)

6. If --auto-accept was passed: skip to step 8

7. Show the user a table:
   `Date | Amount | Payee | Category | Memo (truncated) | Source (rule/AI)`
   Ask user to approve or adjust

8. Write the final categorized transactions back to `baneco/transactions.json`, then import to YNAB:
   `.venv/bin/python -c "import json, sys; from baneco import import_to_ynab; txns = json.loads(sys.stdin.read()); result = import_to_ynab(txns); print(json.dumps(result))"` (pipe the JSON via stdin)
