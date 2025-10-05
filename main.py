# Just run a quick command that execute a sum with no params
# and print the result

import argparse
from tasks.sync_transactions import sync_transactions
from tasks.sync_categories import sync_categories

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YNAB Budget Sync")
    parser.add_argument(
        "--credit-card",
        action="store_true",
        help="Sync only BISA credit card transactions (for late statements)",
    )
    parser.add_argument(
        "--since-date",
        type=str,
        required=True,
        help="Start date for syncing transactions (format: YYYY-MM-DD)",
    )
    args = parser.parse_args()

    sync_transactions(only_credit_card=args.credit_card, since_date=args.since_date)
    # sync_categories()
