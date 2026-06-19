import sqlite3
import os
from datetime import datetime, time
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schedule.db")

DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
DAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

LESSON_TYPES = {
    "lecture": "Лекция",
    "seminar": "Семинар",
    "lab": "Лабораторная",
    "practice": "Практика",
    "exam": "Экзамен",
    "consultation": "Консультация"
}

TYPE_COLORS = {
    "lecture": "#3498db",
    "seminar": "#2ecc71",
    "lab": "#e74c3c",
    "practice": "#f39c12",
    "exam": "#9b59b6",
    "consultation": "#1abc9c"
}


class Lesson:
    """Модель занятия"""

    def __init__(self, id: int, name: str, day_of_week: int, start_time: str,
                 end_time: str, lesson_type: str, room: str, color: str = "#3498db"):
        self.id = id
        self.name = name
        self.day_of_week = day_of_week  # 0-6 (Пн-Вс)
        self.start_time = start_time  # "HH:MM"
        self.end_time = end_time
        self.lesson_type = lesson_type
        self.room = room
        self.color = color

    @property
    def start_dt(self) -> time:
        return datetime.strptime(self.start_time, "%H:%M").time()

    @property
    def end_dt(self) -> time:
        return datetime.strptime(self.end_time, "%H:%M").time()

    @property
    def duration_minutes(self) -> int:
        start = datetime.strptime(self.start_time, "%H:%M")
        end = datetime.strptime(self.end_time, "%H:%M")
        return int((end - start).total_seconds() / 60)

    @property
    def type_display(self) -> str:
        return LESSON_TYPES.get(self.lesson_type, self.lesson_type)


class ScheduleEngine:
    """Бизнес-логика расписания"""

    @staticmethod
    def validate_time(start_time: str, end_time: str) -> bool:
        """Проверка корректности времени"""
        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")
            return end > start
        except ValueError:
            return False

    @staticmethod
    def check_overlap(existing_lessons: List[Lesson], new_lesson: Lesson, exclude_id: int = None) -> bool:
        """Проверка пересечения с существующими занятиями в тот же день"""
        new_start = datetime.strptime(new_lesson.start_time, "%H:%M")
        new_end = datetime.strptime(new_lesson.end_time, "%H:%M")

        for lesson in existing_lessons:
            if lesson.id == exclude_id:
                continue
            if lesson.day_of_week != new_lesson.day_of_week:
                continue

            existing_start = datetime.strptime(lesson.start_time, "%H:%M")
            existing_end = datetime.strptime(lesson.end_time, "%H:%M")

            # Проверка пересечения
            if new_start < existing_end and new_end > existing_start:
                return True
        return False

    @staticmethod
    def get_next_lesson(lessons: List[Lesson]) -> Optional[Lesson]:
        """Получить следующее занятие от текущего момента"""
        now = datetime.now()
        current_day = now.weekday()  # 0=Пн
        current_time = now.time()

        # Собираем все занятия на сегодня и ближайшие дни
        candidates = []
        for i in range(7):
            day = (current_day + i) % 7
            day_lessons = [l for l in lessons if l.day_of_week == day]

            for lesson in day_lessons:
                lesson_start = datetime.strptime(lesson.start_time, "%H:%M").time()

                if i == 0 and lesson_start <= current_time:
                    continue  # Пропускаем уже начавшиеся сегодня

                candidates.append((i, lesson))
                break  # Берём первое занятие дня

        if not candidates:
            return None

        # Сортируем по приоритету: сегодня сначала, потом по времени
        candidates.sort(key=lambda x: (x[0], datetime.strptime(x[1].start_time, "%H:%M")))
        return candidates[0][1]

    @staticmethod
    def get_countdown(next_lesson: Lesson) -> str:
        """Получить строку обратного отсчёта"""
        now = datetime.now()
        current_day = now.weekday()

        days_until = (next_lesson.day_of_week - current_day) % 7
        if days_until == 0:
            # Сегодня
            lesson_start = datetime.strptime(next_lesson.start_time, "%H:%M")
            today_start = lesson_start.replace(year=now.year, month=now.month, day=now.day)
            delta = today_start - now
        else:
            # В другой день
            from datetime import timedelta
            target_date = now.date() + timedelta(days=days_until)
            lesson_start = datetime.strptime(next_lesson.start_time, "%H:%M")
            target_datetime = datetime.combine(target_date, lesson_start.time())
            delta = target_datetime - now

        if delta.total_seconds() <= 0:
            return "Сейчас идёт!"

        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м {seconds}с"
        else:
            return f"{minutes}м {seconds}с"


class Storage:
    """Слой хранения данных"""

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                lesson_type TEXT NOT NULL,
                room TEXT,
                color TEXT DEFAULT '#3498db'
            )
        """)
        self.conn.commit()

    def add_lesson(self, name: str, day_of_week: int, start_time: str,
                   end_time: str, lesson_type: str, room: str, color: str = "#3498db") -> int:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO lessons (name, day_of_week, start_time, end_time, lesson_type, room, color)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, day_of_week, start_time, end_time, lesson_type, room, color))
        self.conn.commit()
        return cur.lastrowid

    def update_lesson(self, lesson_id: int, name: str, day_of_week: int, start_time: str,
                      end_time: str, lesson_type: str, room: str, color: str):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE lessons 
            SET name=?, day_of_week=?, start_time=?, end_time=?, lesson_type=?, room=?, color=?
            WHERE id=?
        """, (name, day_of_week, start_time, end_time, lesson_type, room, color, lesson_id))
        self.conn.commit()

    def delete_lesson(self, lesson_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM lessons WHERE id=?", (lesson_id,))
        self.conn.commit()

    def get_all_lessons(self) -> List[Lesson]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lessons ORDER BY day_of_week, start_time")
        rows = cur.fetchall()
        return [Lesson(**dict(row)) for row in rows]

    def get_lesson(self, lesson_id: int) -> Optional[Lesson]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
        row = cur.fetchone()
        if row:
            return Lesson(**dict(row))
        return None

    def get_lessons_by_day(self, day_of_week: int) -> List[Lesson]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lessons WHERE day_of_week=? ORDER BY start_time", (day_of_week,))
        rows = cur.fetchall()
        return [Lesson(**dict(row)) for row in rows]

    def get_total_hours(self) -> int:
        """Общее количество часов в неделю"""
        lessons = self.get_all_lessons()
        return sum(l.duration_minutes for l in lessons) // 60

    def get_hours_by_day(self) -> List[int]:
        """Часы по дням недели"""
        result = [0] * 7
        lessons = self.get_all_lessons()
        for lesson in lessons:
            result[lesson.day_of_week] += lesson.duration_minutes / 60
        return result

    def get_hours_by_type(self) -> dict:
        """Часы по типам занятий"""
        result = {}
        lessons = self.get_all_lessons()
        for lesson in lessons:
            type_name = lesson.type_display
            result[type_name] = result.get(type_name, 0) + lesson.duration_minutes / 60
        return result

    def close(self):
        self.conn.close()