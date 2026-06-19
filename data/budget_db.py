import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "budget.db")

DEFAULT_CATEGORIES = [
    ("🍔 Еда", "expense"),
    (" Транспорт", "expense"),
    ("🎮 Развлечения", "expense"),
    ("🏠 Жильё", "expense"),
    ("👕 Одежда", "expense"),
    ("💊 Здоровье", "expense"),
    (" Стипендия", "income"),
    ("💼 Подработка", "income"),
    (" Подарки", "income"),
]


class BudgetDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._seed_categories()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                category_id INTEGER,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline TEXT,
                created_date TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _seed_categories(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM categories")
        if cur.fetchone()[0] == 0:
            for name, ctype in DEFAULT_CATEGORIES:
                cur.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, ctype))
            self.conn.commit()

    # --- Категории ---
    def get_categories(self, ctype=None):
        cur = self.conn.cursor()
        if ctype:
            cur.execute("SELECT * FROM categories WHERE type=? ORDER BY name", (ctype,))
        else:
            cur.execute("SELECT * FROM categories ORDER BY type, name")
        return cur.fetchall()

    def add_category(self, name, ctype):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, ctype))
        self.conn.commit()
        return cur.lastrowid

    def delete_category(self, cat_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        self.conn.commit()

    # --- Транзакции ---
    def add_transaction(self, ctype, category_id, amount, description):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions (type, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (ctype, category_id, float(amount), description, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        self.conn.commit()

    def get_balance(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions")
        return cur.fetchone()[0]

    def get_recent_transactions(self, limit=10):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT t.*, c.name as category_name 
            FROM transactions t 
            LEFT JOIN categories c ON t.category_id = c.id 
            ORDER BY t.id DESC LIMIT ?
        """, (limit,))
        return cur.fetchall()

    def get_month_expenses_by_category(self):
        """Расходы по категориям за текущий месяц"""
        cur = self.conn.cursor()
        month_start = datetime.now().strftime("%Y-%m-01")
        cur.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type='expense' AND t.date >= ?
            GROUP BY c.name
            ORDER BY total DESC
        """, (month_start,))
        return cur.fetchall()

    # --- Цели ---
    def get_goals(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM goals ORDER BY created_date DESC")
        return cur.fetchall()

    def add_goal(self, name, target_amount, deadline):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO goals (name, target_amount, deadline, created_date) VALUES (?, ?, ?, ?)",
            (name, float(target_amount), deadline, datetime.now().strftime("%Y-%m-%d"))
        )
        self.conn.commit()
        return cur.lastrowid

    def update_goal_amount(self, goal_id, new_amount):
        cur = self.conn.cursor()
        cur.execute("UPDATE goals SET current_amount=? WHERE id=?", (float(new_amount), goal_id))
        self.conn.commit()

    def delete_goal(self, goal_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM goals WHERE id=?", (goal_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()