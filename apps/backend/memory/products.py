from typing import Optional

from . import _connection


def add_product(name: str, store: str = "", price: Optional[float] = None) -> dict:
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO products (name, store, status, price, sold_count, created_at) VALUES (?, ?, 'building', ?, 0, ?)",
            (name, store, price, _connection.now()),
        )
        row_id = cur.lastrowid
    row = get_product_by_id(row_id)
    assert row is not None
    return row


def get_product_by_id(product_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return dict(row) if row else None


def find_product_by_name(name: str) -> Optional[dict]:
    """Match product name substring — chat translator only."""
    if not name:
        return None
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM products WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"%{name}%",),
        ).fetchone()
    return dict(row) if row else None


def ship_product(name: str) -> bool:
    with _connection.connect() as con:
        cur = con.execute("SELECT id FROM products WHERE name LIKE ? LIMIT 1", (f"%{name}%",))
        row = cur.fetchone()
        if row is None:
            return False
        con.execute("UPDATE products SET status='shipped' WHERE id=?", (row[0],))
    return True


def log_sale(name: str) -> bool:
    with _connection.connect() as con:
        cur = con.execute("SELECT id FROM products WHERE name LIKE ? LIMIT 1", (f"%{name}%",))
        row = cur.fetchone()
        if row is None:
            return False
        con.execute("UPDATE products SET sold_count = sold_count + 1 WHERE id=?", (row[0],))
    return True


def get_products() -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]
