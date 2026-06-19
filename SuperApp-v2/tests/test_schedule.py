import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.schedule_db import Storage, ScheduleEngine, Lesson


class TestScheduleEngine(unittest.TestCase):
    def test_validate_time_correct(self):
        self.assertTrue(ScheduleEngine.validate_time("09:00", "10:30"))
        self.assertTrue(ScheduleEngine.validate_time("14:00", "15:45"))

    def test_validate_time_incorrect(self):
        self.assertFalse(ScheduleEngine.validate_time("10:30", "09:00"))
        self.assertFalse(ScheduleEngine.validate_time("invalid", "10:00"))

    def test_check_overlap_no_overlap(self):
        existing = [Lesson(1, "Математика", 0, "09:00", "10:30", "lecture", "101")]
        new_lesson = Lesson(2, "Физика", 0, "11:00", "12:30", "lecture", "102")
        self.assertFalse(ScheduleEngine.check_overlap(existing, new_lesson))

    def test_check_overlap_with_overlap(self):
        existing = [Lesson(1, "Математика", 0, "09:00", "10:30", "lecture", "101")]
        new_lesson = Lesson(2, "Физика", 0, "10:00", "11:30", "lecture", "102")
        self.assertTrue(ScheduleEngine.check_overlap(existing, new_lesson))

    def test_check_overlap_different_days(self):
        existing = [Lesson(1, "Математика", 0, "09:00", "10:30", "lecture", "101")]
        new_lesson = Lesson(2, "Физика", 1, "09:00", "10:30", "lecture", "102")
        self.assertFalse(ScheduleEngine.check_overlap(existing, new_lesson))

    def test_get_countdown(self):
        # Создаём занятие на завтра
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).weekday()
        lesson = Lesson(1, "Тест", tomorrow, "10:00", "11:00", "lecture", "101")
        countdown = ScheduleEngine.get_countdown(lesson)
        self.assertIsInstance(countdown, str)
        self.assertTrue(len(countdown) > 0)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.storage = Storage()
        cur = self.storage.conn.cursor()
        cur.execute("DELETE FROM lessons")
        self.storage.conn.commit()

    def tearDown(self):
        self.storage.close()
        if os.path.exists("schedule.db"):
            os.remove("schedule.db")

    def test_add_lesson(self):
        lesson_id = self.storage.add_lesson("Математика", 0, "09:00", "10:30", "lecture", "101")
        self.assertIsInstance(lesson_id, int)
        lesson = self.storage.get_lesson(lesson_id)
        self.assertEqual(lesson.name, "Математика")

    def test_update_lesson(self):
        lesson_id = self.storage.add_lesson("Математика", 0, "09:00", "10:30", "lecture", "101")
        self.storage.update_lesson(lesson_id, "Алгебра", 1, "11:00", "12:30", "seminar", "102", "#2ecc71")
        lesson = self.storage.get_lesson(lesson_id)
        self.assertEqual(lesson.name, "Алгебра")
        self.assertEqual(lesson.day_of_week, 1)

    def test_delete_lesson(self):
        lesson_id = self.storage.add_lesson("Тест", 0, "09:00", "10:30", "lecture", "101")
        self.storage.delete_lesson(lesson_id)
        self.assertIsNone(self.storage.get_lesson(lesson_id))

    def test_get_lessons_by_day(self):
        self.storage.add_lesson("Понедельник 1", 0, "09:00", "10:30", "lecture", "101")
        self.storage.add_lesson("Понедельник 2", 0, "11:00", "12:30", "seminar", "102")
        self.storage.add_lesson("Вторник", 1, "09:00", "10:30", "lecture", "103")

        monday_lessons = self.storage.get_lessons_by_day(0)
        self.assertEqual(len(monday_lessons), 2)

    def test_get_total_hours(self):
        self.storage.add_lesson("Тест 1", 0, "09:00", "10:30", "lecture", "101")  # 1.5 часа
        self.storage.add_lesson("Тест 2", 1, "11:00", "12:30", "seminar", "102")  # 1.5 часа
        total = self.storage.get_total_hours()
        self.assertEqual(total, 3)

    def test_get_hours_by_day(self):
        self.storage.add_lesson("Пн", 0, "09:00", "10:30", "lecture", "101")
        self.storage.add_lesson("Вт", 1, "11:00", "13:00", "seminar", "102")
        hours = self.storage.get_hours_by_day()
        self.assertAlmostEqual(hours[0], 1.5)
        self.assertAlmostEqual(hours[1], 2.0)


if __name__ == "__main__":
    unittest.main()