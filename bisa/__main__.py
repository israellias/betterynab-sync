"""
BISA bank transaction exporter and YNAB importer.

Full pipeline: Playwright login (manual 2FA) -> navigate to account ->
filter by date -> download CSV -> convert to YNAB format -> bulk import to YNAB API.

Usage:
    python -m bisa                          # Full pipeline
    python -m bisa --since-date 2026-02-01  # Override start date
    python -m bisa --export-only            # Just download CSV
    python -m bisa --dry-run                # Export + convert, save JSON
    python -m bisa --reset                  # Clear browser state
"""

import sys

from bisa.config import BisaConfig
from bisa.pipeline import BisaPipeline


def main():
    config = BisaConfig()
    pipeline = BisaPipeline(config)

    if "--reset" in sys.argv:
        pipeline.exporter.reset()
        if len(sys.argv) == 2:
            return

    since_date = None
    if "--since-date" in sys.argv:
        idx = sys.argv.index("--since-date")
        since_date = sys.argv[idx + 1]

    export_only = "--export-only" in sys.argv
    dry_run = "--dry-run" in sys.argv

    pipeline.run(since_date=since_date, export_only=export_only, dry_run=dry_run)


if __name__ == "__main__":
    main()
