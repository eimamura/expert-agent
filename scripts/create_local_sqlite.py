from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("data/local.sqlite")


SEED_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    phone TEXT,
    name TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    status TEXT NOT NULL,
    acquisition_channel TEXT
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    order_total REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

INSERT INTO customers (
    customer_id, email, phone, name, signup_date, status, acquisition_channel
) VALUES
    (1, 'jane@example.com', '+1-555-0101', 'Jane Lee', '2026-01-12', 'active', 'paid_search'),
    (2, 'marco@example.com', '+1-555-0102', 'Marco Silva', '2026-02-03', 'active', 'organic'),
    (3, 'sam@example.com', '+1-555-0103', 'Sam Rivera', '2026-02-20', 'paused', 'partner');

INSERT INTO products (
    product_id, sku, product_name, category, active
) VALUES
    (101, 'SUB-BASIC', 'Basic Subscription', 'subscription', 1),
    (102, 'SUB-PRO', 'Pro Subscription', 'subscription', 1),
    (201, 'ADD-SUPPORT', 'Priority Support Add-on', 'addon', 1);

INSERT INTO orders (
    order_id, customer_id, order_date, order_total, status
) VALUES
    (1001, 1, '2026-03-01', 29.00, 'paid'),
    (1002, 1, '2026-04-01', 49.00, 'paid'),
    (1003, 2, '2026-04-05', 49.00, 'paid'),
    (1004, 3, '2026-04-08', 29.00, 'refunded');

INSERT INTO order_items (
    order_item_id, order_id, product_id, quantity, unit_price
) VALUES
    (1, 1001, 101, 1, 29.00),
    (2, 1002, 102, 1, 49.00),
    (3, 1003, 102, 1, 49.00),
    (4, 1004, 101, 1, 29.00);
"""


def create_local_sqlite(path: Path = DEFAULT_DB_PATH, *, force: bool = False) -> Path:
    if path.exists():
        if not force:
            raise FileExistsError(f"SQLite database already exists: {path}")
        path.unlink()

    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SEED_SQL)
        conn.commit()
    finally:
        conn.close()
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local seeded SQLite database for Phase 1.")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite database path. Defaults to {DEFAULT_DB_PATH}.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite the database if it already exists.")
    args = parser.parse_args()

    path = create_local_sqlite(args.path, force=args.force)
    print(f"Created SQLite database at {path}")


if __name__ == "__main__":
    main()
