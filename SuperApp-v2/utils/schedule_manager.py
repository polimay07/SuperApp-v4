import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from datetime import datetime
from data.schedule_db import Storage, ScheduleEngine, Lesson, DAY_NAMES, DAY_SHORT, LESSON_TYPES, TYPE_COLORS


class ScheduleManagerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.storage = Storage()
        self.engine = ScheduleEngine()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Заголовок + кнопки
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=" Расписание занятий",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(btn_frame, text="➕ Добавить занятие", command=self._show_add_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📊 Аналитика", command=self._show_analytics).pack(side="left", padx=5)

        # Таймер обратного отсчёта
        self.timer_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=10)
        self.timer_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            self.timer_frame, text="⏰ До следующей пары:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        self.next_lesson_label = ctk.CTkLabel(
            self.timer_frame, text="Загрузка...",
            font=ctk.CTkFont(size=18)
        )
        self.next_lesson_label.pack(pady=5)

        self.countdown_label = ctk.CTkLabel(
            self.timer_frame, text="--:--:--",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#f39c12"
        )
        self.countdown_label.pack(pady=5)

        # Сетка недели
        self.week_frame = ctk.CTkScrollableFrame(self)
        self.week_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.week_frame.grid_columnconfigure(0, weight=1)

        self.refresh()
        self._update_timer()

    def refresh(self):
        """Обновить отображение расписания"""
        for widget in self.week_frame.winfo_children():
            widget.destroy()

        lessons = self.storage.get_all_lessons()

        for day_idx in range(7):
            day_frame = ctk.CTkFrame(self.week_frame, fg_color="gray20", corner_radius=10)
            day_frame.pack(fill="x", pady=5)
            day_frame.grid_columnconfigure(1, weight=1)

            # Заголовок дня
            day_header = ctk.CTkFrame(day_frame, fg_color="transparent")
            day_header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

            ctk.CTkLabel(
                day_header, text=f"{DAY_NAMES[day_idx]}",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(side="left")

            day_lessons = [l for l in lessons if l.day_of_week == day_idx]
            ctk.CTkLabel(
                day_header, text=f"({len(day_lessons)} занятий)",
                font=ctk.CTkFont(size=14), text_color="gray"
            ).pack(side="right")

            # Список занятий
            if not day_lessons:
                ctk.CTkLabel(
                    day_frame, text="Нет занятий",
                    font=ctk.CTkFont(size=14), text_color="gray"
                ).grid(row=1, column=0, padx=15, pady=10, sticky="w")
            else:
                for i, lesson in enumerate(day_lessons):
                    lesson_card = ctk.CTkFrame(day_frame, fg_color="gray15", corner_radius=8)
                    lesson_card.grid(row=i + 1, column=0, sticky="ew", padx=15, pady=3)
                    lesson_card.grid_columnconfigure(0, weight=1)

                    # Цветовая метка
                    color_bar = ctk.CTkFrame(lesson_card, width=6, fg_color=lesson.color, corner_radius=3)
                    color_bar.grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=10, sticky="ns")

                    # Информация
                    info_frame = ctk.CTkFrame(lesson_card, fg_color="transparent")
                    info_frame.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))

                    ctk.CTkLabel(
                        info_frame, text=lesson.name,
                        font=ctk.CTkFont(size=16, weight="bold")
                    ).pack(anchor="w")

                    ctk.CTkLabel(
                        info_frame,
                        text=f"{lesson.start_time} - {lesson.end_time} | {lesson.type_display} | Ауд. {lesson.room}",
                        font=ctk.CTkFont(size=13), text_color="gray"
                    ).pack(anchor="w")

                    # Кнопки действий
                    action_frame = ctk.CTkFrame(lesson_card, fg_color="transparent")
                    action_frame.grid(row=0, column=2, padx=10, pady=10, sticky="e")

                    ctk.CTkButton(
                        action_frame, text="✏️", width=40, fg_color="gray",
                        command=lambda lid=lesson.id: self._show_edit_dialog(lid)
                    ).pack(side="left", padx=3)

                    ctk.CTkButton(
                        action_frame, text="🗑", width=40, fg_color="#e74c3c",
                        command=lambda lid=lesson.id: self._delete_lesson(lid)
                    ).pack(side="left", padx=3)

    def _update_timer(self):
        """Обновить таймер обратного отсчёта"""
        lessons = self.storage.get_all_lessons()
        next_lesson = self.engine.get_next_lesson(lessons)

        if next_lesson:
            day_name = DAY_NAMES[next_lesson.day_of_week]
            self.next_lesson_label.configure(
                text=f"{next_lesson.name} ({day_name}, {next_lesson.start_time})"
            )
            countdown = self.engine.get_countdown(next_lesson)
            self.countdown_label.configure(text=countdown)
        else:
            self.next_lesson_label.configure(text="Нет предстоящих занятий")
            self.countdown_label.configure(text="🎉")

        # Запланировать следующее обновление через 1 секунду
        self.after(1000, self._update_timer)

    def _show_add_dialog(self):
        """Диалог добавления занятия"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Новое занятие")
        dialog.geometry("500x500")
        dialog.grab_set()

        # Название
        ctk.CTkLabel(dialog, text="Название:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(20, 5), anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=460)
        name_entry.pack(padx=20)

        # День недели
        ctk.CTkLabel(dialog, text="День недели:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        day_var = ctk.StringVar(value="0")
        day_combo = ctk.CTkComboBox(dialog, values=DAY_NAMES, variable=day_var, width=460)
        day_combo.pack(padx=20)

        # Время
        time_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        time_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(time_frame, text="Начало:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        start_entry = ctk.CTkEntry(time_frame, placeholder_text="09:00", width=100)
        start_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(time_frame, text="Конец:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        end_entry = ctk.CTkEntry(time_frame, placeholder_text="10:30", width=100)
        end_entry.pack(side="left")

        # Тип занятия
        ctk.CTkLabel(dialog, text="Тип занятия:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        type_var = ctk.StringVar(value="lecture")
        type_combo = ctk.CTkComboBox(
            dialog,
            values=list(LESSON_TYPES.values()),
            variable=type_var,
            width=460
        )
        type_combo.pack(padx=20)

        # Аудитория
        ctk.CTkLabel(dialog, text="Аудитория:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        room_entry = ctk.CTkEntry(dialog, placeholder_text="101", width=460)
        room_entry.pack(padx=20)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите название")
                return

            day_idx = DAY_NAMES.index(day_var.get())
            start_time = start_entry.get().strip()
            end_time = end_entry.get().strip()

            # Валидация времени
            if not self.engine.validate_time(start_time, end_time):
                messagebox.showerror("Ошибка", "Некорректное время. Конец должен быть позже начала.")
                return

            # Получаем тип занятия по отображаемому имени
            type_display = type_var.get()
            lesson_type = [k for k, v in LESSON_TYPES.items() if v == type_display][0]
            color = TYPE_COLORS.get(lesson_type, "#3498db")

            room = room_entry.get().strip()

            # Создаём временный объект для проверки пересечений
            temp_lesson = Lesson(0, name, day_idx, start_time, end_time, lesson_type, room, color)
            existing = self.storage.get_all_lessons()

            if self.engine.check_overlap(existing, temp_lesson):
                messagebox.showerror("Ошибка", "Это занятие пересекается с другим в тот же день!")
                return

            self.storage.add_lesson(name, day_idx, start_time, end_time, lesson_type, room, color)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Создать", command=save, width=460).pack(padx=20, pady=20)

    def _show_edit_dialog(self, lesson_id):
        """Диалог редактирования занятия"""
        lesson = self.storage.get_lesson(lesson_id)
        if not lesson:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактировать занятие")
        dialog.geometry("500x500")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Название:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(20, 5), anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=460)
        name_entry.insert(0, lesson.name)
        name_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="День недели:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        day_var = ctk.StringVar(value=DAY_NAMES[lesson.day_of_week])
        day_combo = ctk.CTkComboBox(dialog, values=DAY_NAMES, variable=day_var, width=460)
        day_combo.pack(padx=20)

        time_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        time_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(time_frame, text="Начало:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        start_entry = ctk.CTkEntry(time_frame, width=100)
        start_entry.insert(0, lesson.start_time)
        start_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(time_frame, text="Конец:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        end_entry = ctk.CTkEntry(time_frame, width=100)
        end_entry.insert(0, lesson.end_time)
        end_entry.pack(side="left")

        ctk.CTkLabel(dialog, text="Тип занятия:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        type_display = lesson.type_display
        type_var = ctk.StringVar(value=type_display)
        type_combo = ctk.CTkComboBox(
            dialog,
            values=list(LESSON_TYPES.values()),
            variable=type_var,
            width=460
        )
        type_combo.pack(padx=20)

        ctk.CTkLabel(dialog, text="Аудитория:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        room_entry = ctk.CTkEntry(dialog, width=460)
        room_entry.insert(0, lesson.room)
        room_entry.pack(padx=20)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите название")
                return

            day_idx = DAY_NAMES.index(day_var.get())
            start_time = start_entry.get().strip()
            end_time = end_entry.get().strip()

            if not self.engine.validate_time(start_time, end_time):
                messagebox.showerror("Ошибка", "Некорректное время.")
                return

            type_display = type_var.get()
            lesson_type = [k for k, v in LESSON_TYPES.items() if v == type_display][0]
            color = TYPE_COLORS.get(lesson_type, "#3498db")
            room = room_entry.get().strip()

            temp_lesson = Lesson(lesson_id, name, day_idx, start_time, end_time, lesson_type, room, color)
            existing = self.storage.get_all_lessons()

            if self.engine.check_overlap(existing, temp_lesson, exclude_id=lesson_id):
                messagebox.showerror("Ошибка", "Пересечение с другим занятием!")
                return

            self.storage.update_lesson(lesson_id, name, day_idx, start_time, end_time, lesson_type, room, color)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Сохранить", command=save, width=460).pack(padx=20, pady=20)

    def _delete_lesson(self, lesson_id):
        if messagebox.askyesno("Удаление", "Удалить это занятие?"):
            self.storage.delete_lesson(lesson_id)
            self.refresh()

    def _show_analytics(self):
        """Показать аналитику нагрузки"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Аналитика учебной нагрузки")
        dialog.geometry("800x600")
        dialog.grab_set()

        # Общая информация
        total_hours = self.storage.get_total_hours()
        ctk.CTkLabel(
            dialog, text=f"📚 Общая нагрузка: {total_hours} часов в неделю",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # График по дням
        chart_frame = ctk.CTkFrame(dialog)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        hours_by_day = self.storage.get_hours_by_day()

        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=100)

        # График по дням
        ax1.bar(DAY_SHORT, hours_by_day, color='#3498db', alpha=0.7)
        ax1.set_title("Нагрузка по дням", fontsize=12, color='white')
        ax1.set_xlabel("День", color='white')
        ax1.set_ylabel("Часы", color='white')
        ax1.tick_params(colors='white')
        ax1.grid(True, alpha=0.3)

        # График по типам
        hours_by_type = self.storage.get_hours_by_type()
        if hours_by_type:
            labels = list(hours_by_type.keys())
            sizes = list(hours_by_type.values())
            colors = list(TYPE_COLORS.values())[:len(labels)]
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, textprops={'color': 'white'})
            ax2.set_title("Распределение по типам", fontsize=12, color='white')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def destroy(self):
        self.storage.close()
        super().destroy()