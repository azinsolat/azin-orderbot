import sqlite3
from datetime import datetime

DB_PATH = "orders.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        # جدول سفارش‌ها
        c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            national_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        );
        """)

        # جدول محصولات
        c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        """)

        # جدول سبد خرید
        c.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        );
        """)

        # جدول آیتم‌های هر سفارش
        c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_title TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL
        );
        """)

        conn.commit()


# ---------------- سفارش‌ها ----------------

def create_order(
    user_id: int,
    national_id: str,
    full_name: str,
    phone: str,
    address: str,
    description: str
):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO orders (user_id, national_id, full_name, phone, address, description, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
        """, (user_id, national_id, full_name, phone, address, description, datetime.utcnow().isoformat()))
        conn.commit()
        return cur.lastrowid


def list_orders(limit: int = 20, offset: int = 0):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, national_id, full_name, phone, address, description, status, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return cur.fetchall()


def get_order(order_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, national_id, full_name, phone, address, description, status, created_at
            FROM orders
            WHERE id=?
        """, (order_id,))
        return cur.fetchone()


def update_order_status(order_id: int, new_status: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        conn.commit()
        return cur.rowcount


# لیست آیتم‌های یک سفارش
def get_order_items(order_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT product_title, quantity, price
            FROM order_items
            WHERE order_id=?
        """, (order_id,))
        return cur.fetchall()


# ---------------- محصولات ----------------

def create_product(code: str, title: str, price: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO products (code, title, price, is_active)
        VALUES (?, ?, ?, 1)
        """, (code, title, price))
        conn.commit()
        return cur.lastrowid


def get_product_by_code(code: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, title, price, is_active
            FROM products
            WHERE code=?
        """, (code,))
        return cur.fetchone()


# ---------------- سبد خرید ----------------

def add_to_cart(user_id: int, product_id: int):
    """اگر این محصول در سبد بود، تعدادش +۱ می‌شود؛ اگر نبود، ردیف جدید ساخته می‌شود."""
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, quantity
            FROM cart
            WHERE user_id=? AND product_id=?
        """, (user_id, product_id))
        row = cur.fetchone()

        if row:
            cart_id, qty = row
            new_qty = qty + 1
            cur.execute("UPDATE cart SET quantity=? WHERE id=?", (new_qty, cart_id))
        else:
            cur.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, 1)
            """, (user_id, product_id))

        conn.commit()


def get_cart(user_id: int):
    """
    برمی‌گرداند لیست:
    (cart_id, product_id, quantity, title, price)
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.id,
                c.product_id,
                c.quantity,
                p.title,
                p.price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id=?
            ORDER BY c.id ASC
        """, (user_id,))
        return cur.fetchall()


def update_cart_item_quantity(cart_id: int, new_quantity: int):
    with get_conn() as conn:
        cur = conn.cursor()
        if new_quantity <= 0:
            cur.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        else:
            cur.execute("UPDATE cart SET quantity=? WHERE id=?", (new_quantity, cart_id))
        conn.commit()


def remove_cart_item(cart_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        conn.commit()


def clear_cart(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        conn.commit()


# ذخیره‌ی آیتم‌های سبد خرید در جدول order_items
def save_cart_to_order(order_id: int, user_id: int):
    """
    آیتم‌های سبد خرید این کاربر را می‌خواند
    و برای این سفارش، در order_items ذخیره می‌کند.
    """
    cart_items = get_cart(user_id)
    if not cart_items:
        return

    with get_conn() as conn:
        cur = conn.cursor()
        for cart_id, product_id, qty, title, price in cart_items:
            cur.execute("""
                INSERT INTO order_items (order_id, product_title, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, title, qty, price))
        conn.commit()


def list_orders_by_user(user_id: int, limit: int = 10, offset: int = 0):
    """لیست سفارش‌های یک کاربر خاص را برمی‌گرداند."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, national_id, full_name, phone, address, description, status, created_at
            FROM orders
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        return cur.fetchall()