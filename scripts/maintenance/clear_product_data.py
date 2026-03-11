#!/usr/bin/env python3
"""Clear product-related tables for local dev testing.

Safety:
- Requires --confirm with a specific phrase.
- Prints target DB path before running.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

CONFIRM_PHRASE = "CLEAR_PRODUCTS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clear product-related tables")
    parser.add_argument(
        "--confirm",
        help=f"Type {CONFIRM_PHRASE} to proceed",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.confirm != CONFIRM_PHRASE:
        print("Confirmation phrase mismatch. No changes made.")
        return 1

    db_path = Path(__file__).resolve().parents[2] / "db" / "pricegoblin.db"
    print(f"Target DB: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=OFF")
    for table in ("price_entries", "tracking", "products"):
        cur.execute(f"DELETE FROM {table}")
    conn.commit()
    cur.execute("PRAGMA foreign_keys=ON")
    conn.close()

    print("Cleared: price_entries, tracking, products")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
