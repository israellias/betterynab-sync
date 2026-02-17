"""
Baneco bank transaction exporter and YNAB importer.

Full pipeline: export transactions from benet.baneco.com.bo via Playwright,
convert to YNAB format with payee matching, and bulk import to YNAB API.

Usage:
    python -m baneco                          # Full pipeline
    python -m baneco --since-date 2026-02-01  # Override start date
    python -m baneco --export-only            # Just download CSV
    python -m baneco --reset                  # Clear browser state
"""

import sys

from baneco.config import BanecoConfig
from baneco.pipeline import BanecoPipeline


def main():
    config = BanecoConfig()
    pipeline = BanecoPipeline(config)

    if "--reset" in sys.argv:
        pipeline.exporter.reset()

    since_date = None
    if "--since-date" in sys.argv:
        idx = sys.argv.index("--since-date")
        since_date = sys.argv[idx + 1]

    export_only = "--export-only" in sys.argv
    dry_run = "--dry-run" in sys.argv

    pipeline.run(since_date=since_date, export_only=export_only, dry_run=dry_run)


if __name__ == "__main__":
    main()
