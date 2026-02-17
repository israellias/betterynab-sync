import json
import os

from baneco.config import BanecoConfig
from baneco.converter import BanecoConverter
from baneco.exporter import BanecoExporter
from baneco.importer import YNABImporter

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_PATH = os.path.join(SCRIPT_DIR, "baneco_transactions.json")


class BanecoPipeline:
    def __init__(self, config: BanecoConfig):
        self.config = config
        self.exporter = BanecoExporter(config)
        self.converter = BanecoConverter()
        self.importer = YNABImporter(config.ynab_budget_name, config.ynab_account_id)

    def run(self, since_date: str = None, export_only: bool = False, dry_run: bool = False):
        """Execute the full Baneco → YNAB pipeline."""
        # Step 1: Determine since_date (before export so we can set the date range)
        if not export_only:
            if not since_date:
                since_date = self.importer.get_last_transaction_date()
                if since_date:
                    print(f"Last YNAB transaction: {since_date}", flush=True)
                else:
                    print("No existing transactions found. Importing all.", flush=True)
            else:
                print(f"Using override since-date: {since_date}", flush=True)

        # Step 2: Export CSV from Baneco (with date range when available)
        csv_path = self.exporter.export(since_date=since_date)

        if export_only:
            return

        # Step 3: Convert CSV to YNAB transactions
        transactions = self.converter.convert(
            csv_path,
            account_id=self.config.ynab_account_id,
            since_date=since_date,
        )
        print(f"Converted {len(transactions)} transactions from CSV.", flush=True)

        if dry_run:
            with open(TRANSACTIONS_PATH, "w") as f:
                json.dump(transactions, f, indent=2)
            print(f"Dry run: saved {len(transactions)} transactions to {TRANSACTIONS_PATH}", flush=True)
            return

        # Step 4: Upload to YNAB
        self.importer.import_transactions(transactions)
