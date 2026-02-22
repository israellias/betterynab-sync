"""
Binance P2P transaction exporter and YNAB importer.

Full pipeline: intercept Binance P2P order history via Playwright,
convert SELL USDT→BOB trades to YNAB format, and bulk import to YNAB API.

Usage:
    python -m binance                          # Full pipeline
    python -m binance --since-date 2026-02-01  # Override start date
    python -m binance --export-only            # Just download JSON
    python -m binance --dry-run                # Export + convert, save JSON
    python -m binance --reset                  # Clear browser state
"""

import sys

from binance.config import BinanceConfig
from binance.pipeline import BinancePipeline


def main():
    config = BinanceConfig()
    pipeline = BinancePipeline(config)

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
