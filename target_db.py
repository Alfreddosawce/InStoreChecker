import sqlite3

DB_NAME = "target_inventory.db"
from pathlib import Path

def get_connection():
    return sqlite3.connect(DB_NAME)

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    #create tables

    #product(tcin, title, price)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
    tcin INTEGER PRIMARY KEY,
    title TEXT,
    price REAL
    )
    """)

    #stores(store_id, location_name, address)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stores(
    store_id INTEGER PRIMARY KEY,
    location_name TEXT,
    address TEXT
    )
    """)

    #stock(id, tcin, store_id, quantity, availability, last_available_at, checked_at)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tcin INTEGER,
    store_id INTEGER,
    quantity INTEGER,
    availability BOOLEAN,
    last_available_at DATETIME,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (tcin) REFERENCES products(tcin),
    UNIQUE (tcin, store_id)
    )
    """)

    conn.commit()
    conn.close()

def insert_product(tcin, title=None, price=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO products (tcin, title, price)
        VALUES (?, ?, ?)
        ON CONFLICT(tcin) DO UPDATE SET
            title = excluded.title,
            price = excluded.price
        """,
        (tcin, title, price)
    )
    conn.commit()
    conn.close()


def insert_store(store_id, location_name, address):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO stores (store_id, location_name, address)
        VALUES (?, ?, ?)
        ON CONFLICT(store_id) DO UPDATE SET
            location_name = excluded.location_name,
            address = excluded.address
        """,
        (store_id, location_name, address)
    )

    conn.commit()
    conn.close()



def insert_stock(tcin, store_id, quantity, availability, last_available_at, checked_at):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO stock (tcin, store_id, quantity, availability, last_available_at, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(tcin, store_id) DO UPDATE SET
            quantity = excluded.quantity,
            availability = excluded.availability,
            last_available_at = excluded.last_available_at,
            checked_at = excluded.checked_at
        """,
        (tcin, store_id, quantity, availability, last_available_at, checked_at)
    )

    conn.commit()
    conn.close()

def get_tcins_missing_metadata():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT stock.tcin
        FROM stock
        LEFT JOIN products ON stock.tcin = products.tcin
        WHERE products.tcin IS NULL
    """)

    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

