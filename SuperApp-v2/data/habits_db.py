import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "habits.db")


class HabitsDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#3498db',
                created_date TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('completed', 'skipped')),
                UNIQUE(habit_id, date),
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def add_habit(self, name, description="", color="#3498db"):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO habits (name, description, color, created_date) VALUES (?, ?, ?, ?)",
            (name, description, color, datetime.now().strftime("%Y-%m-%d"))
        )
        self.conn.commit()
        return cur.lastrowid

    def update_habit(self, habit_id, name, description, color):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE habits SET name=?, description=?, color=? WHERE id=?",
            (name, description, color, habit_id)
        )
        self.conn.commit()

    def delete_habit(self, habit_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        self.conn.commit()

    def get_all_habits(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM habits ORDER BY created_date DESC")
        return cur.fetchall()

    def get_habit(self, habit_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM habits WHERE id=?", (habit_id,))
        return cur.fetchone()

    def mark_habit(self, habit_id, date_str, status):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM habit_logs WHERE habit_id=? AND date=?",
            (habit_id, date_str)
        )
        if cur.fetchone():
            raise ValueError(f"Привычка уже отмечена за {date_str}")

        cur.execute(
            "INSERT INTO habit_logs (habit_id, date, status) VALUES (?, ?, ?)",
            (habit_id, date_str, status)
        )
        self.conn.commit()

    def update_habit_status(self, habit_id, date_str, status):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE habit_logs SET status=? WHERE habit_id=? AND date=?",
            (status, habit_id, date_str)
        )
        self.conn.commit()

    def get_log(self, habit_id, date_str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM habit_logs WHERE habit_id=? AND date=?",
            (habit_id, date_str)
        )
        return cur.fetchone()

    def get_logs_for_habit(self, habit_id, days=90):
        cur = self.conn.cursor()
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT * FROM habit_logs WHERE habit_id=? AND date BETWEEN ? AND ? ORDER BY date",
            (habit_id, start_date, end_date)
        )
        return cur.fetchall()

    def get_current_streak(self, habit_id):
        cur = self.conn.cursor()
        streak = 0
        current = datetime.now()

        while True:
            date_str = current.strftime("%Y-%m-%d")
            cur.execute(
                "SELECT status FROM habit_logs WHERE habit_id=? AND date=?",
                (habit_id, date_str)
            )
            row = cur.fetchone()
            if row and row["status"] == "completed":
                streak += 1
                current -= timedelta(days=1)
            else:
                break
        return streak

    def get_best_streak(self, habit_id):
        logs = self.get_logs_for_habit(habit_id, days=3650)
        if not logs:
            return 0

        best = 0
        current = 0
        prev_date = None

        for log in logs:
            log_date = datetime.strptime(log["date"], "%Y-%m-%d").date()
            if log["status"] == "completed":
                if prev_date and (log_date - prev_date).days == 1:
                    current += 1
                else:
                    current = 1
                best = max(best, current)
            else:
                current = 0
            prev_date = log_date

        return best

    def get_completion_rate(self, habit_id, days=30):
        logs = self.get_logs_for_habit(habit_id, days)
        completed = sum(1 for log in logs if log["status"] == "completed")
        return (completed / days * 100) if days > 0 else 0

    def get_total_completed(self, habit_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM habit_logs WHERE habit_id=? AND status='completed'",
            (habit_id,)
        )
        return cur.fetchone()[0]

    def export_data(self, filepath):
        habits = self.get_all_habits()
        data = {"habits": [], "exported_at": datetime.now().isoformat()}

        for h in habits:
            logs = self.get_logs_for_habit(h["id"], days=3650)
            data["habits"].append({
                "name": h["name"],
                "description": h["description"],
                "color": h["color"],
                "created_date": h["created_date"],
                "logs": [
                    {"date": log["date"], "status": log["status"]}
                    for log in logs
                ]
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return len(habits)

    def import_data(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = 0
        for h in data.get("habits", []):
            habit_id = self.add_habit(h["name"], h.get("description", ""), h.get("color", "#3498db"))
            for log in h.get("logs", []):
                try:
                    self.mark_habit(habit_id, log["date"], log["status"])
                except ValueError:
                    pass
            imported += 1

        return imported

    def close(self):
        self.conn.close()