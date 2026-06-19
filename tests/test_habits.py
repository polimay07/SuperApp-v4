import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.habits_db import HabitsDB


class TestHabitsDB(unittest.TestCase):
    def setUp(self):
        self.db = HabitsDB()
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM habit_logs")
        cur.execute("DELETE FROM habits")
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()
        if os.path.exists("habits.db"):
            os.remove("habits.db")

    def test_add_habit(self):
        habit_id = self.db.add_habit("Бег", "Утренний бег 5 км", "#2ecc71")
        self.assertIsInstance(habit_id, int)
        habit = self.db.get_habit(habit_id)
        self.assertEqual(habit["name"], "Бег")
        self.assertEqual(habit["color"], "#2ecc71")

    def test_update_habit(self):
        habit_id = self.db.add_habit("Старое название")
        self.db.update_habit(habit_id, "Новое название", "Новое описание", "#e74c3c")
        habit = self.db.get_habit(habit_id)
        self.assertEqual(habit["name"], "Новое название")
        self.assertEqual(habit["color"], "#e74c3c")

    def test_delete_habit(self):
        habit_id = self.db.add_habit("Тестовая")
        self.db.delete_habit(habit_id)
        self.assertIsNone(self.db.get_habit(habit_id))

    def test_mark_habit_completed(self):
        habit_id = self.db.add_habit("Тест")
        self.db.mark_habit(habit_id, "2026-06-19", "completed")
        log = self.db.get_log(habit_id, "2026-06-19")
        self.assertEqual(log["status"], "completed")

    def test_mark_habit_skipped(self):
        habit_id = self.db.add_habit("Тест")
        self.db.mark_habit(habit_id, "2026-06-19", "skipped")
        log = self.db.get_log(habit_id, "2026-06-19")
        self.assertEqual(log["status"], "skipped")

    def test_duplicate_mark_raises_error(self):
        habit_id = self.db.add_habit("Тест")
        self.db.mark_habit(habit_id, "2026-06-19", "completed")
        with self.assertRaises(ValueError):
            self.db.mark_habit(habit_id, "2026-06-19", "skipped")

    def test_current_streak(self):
        habit_id = self.db.add_habit("Серия")
        today = "2026-06-19"
        for i in range(3):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.db.mark_habit(habit_id, date, "completed")
        self.assertEqual(self.db.get_current_streak(habit_id), 3)

    def test_current_streak_broken(self):
        habit_id = self.db.add_habit("Серия")
        today = datetime.now().strftime("%Y-%m-%d")
        self.db.mark_habit(habit_id, today, "skipped")
        self.assertEqual(self.db.get_current_streak(habit_id), 0)

    def test_best_streak(self):
        habit_id = self.db.add_habit("Серия")
        for i in range(8, 3, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.db.mark_habit(habit_id, date, "completed")
        skip_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        self.db.mark_habit(habit_id, skip_date, "skipped")
        for i in range(2, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.db.mark_habit(habit_id, date, "completed")

        self.assertEqual(self.db.get_best_streak(habit_id), 5)

    def test_completion_rate(self):
        habit_id = self.db.add_habit("Тест")
        for i in range(15):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.db.mark_habit(habit_id, date, "completed")
        rate = self.db.get_completion_rate(habit_id, 30)
        self.assertAlmostEqual(rate, 50.0, places=1)

    def test_export_import(self):
        habit_id = self.db.add_habit("Экспорт тест", "Описание", "#3498db")
        self.db.mark_habit(habit_id, "2026-06-19", "completed")
        self.db.mark_habit(habit_id, "2026-06-18", "skipped")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            count = self.db.export_data(filepath)
            self.assertEqual(count, 1)

            new_db = HabitsDB()
            cur = new_db.conn.cursor()
            cur.execute("DELETE FROM habit_logs")
            cur.execute("DELETE FROM habits")
            new_db.conn.commit()

            imported = new_db.import_data(filepath)
            self.assertEqual(imported, 1)

            habits = new_db.get_all_habits()
            self.assertEqual(len(habits), 1)
            self.assertEqual(habits[0]["name"], "Экспорт тест")

            log = new_db.get_log(habits[0]["id"], "2026-06-19")
            self.assertEqual(log["status"], "completed")
            new_db.close()
        finally:
            os.remove(filepath)


from datetime import datetime, timedelta

if __name__ == "__main__":
    unittest.main()