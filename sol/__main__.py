"""
Banco Sol transaction exporter and YNAB importer.

Full pipeline: export transactions from solnetdigital.bancosol.com.bo via Playwright,
parse PDF extract, convert to YNAB format with payee matching, and bulk import to YNAB API.

Usage:
    python -m sol                          # Full pipeline
    python -m sol --since-date 2026-02-01  # Override start date
    python -m sol --export-only            # Just download PDF
    python -m sol --dry-run                # Export + convert, save JSON
    python -m sol --reset                  # Clear browser state
"""

import sys

from sol.config import SolConfig
from sol.pipeline import SolPipeline


def main():
    config = SolConfig()
    pipeline = SolPipeline(config)

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
