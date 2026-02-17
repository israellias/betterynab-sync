"""Baneco CSV → YNAB CSV converter for manual import."""

import sys

from baneco.converter import BanecoConverter

filename = sys.argv[1]
converter = BanecoConverter()
converter.to_ynab_csv(filename)
