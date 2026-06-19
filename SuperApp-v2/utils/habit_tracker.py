from datetime import datetime, timedelta
from tkinter import filedialog, messagebox

import customtkinter as ctk

from data.habits_db import HabitsDB


class HabitTrackerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db = HabitsDB()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="🎯 Трекер привычек",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(btn_frame, text="📤 Экспорт", command=self._export).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📥 Импорт", command=self._import).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="➕ Новая привычка", command=self._show_add_dialog).pack(side="left", padx=5)

        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.main_container.grid_columnconfigure(0, weight=1)

        self.refresh()

    def refresh(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        habits = self.db.get_all_habits()
        if not habits:
            ctk.CTkLabel(
                self.main_container,
                text="Нет привычек. Создайте первую!",
                font=ctk.CTkFont(size=18), text_color="gray"
            ).pack(pady=60)
            return

        for habit in habits:
            self._render_habit_card(habit)

    def _render_habit_card(self, habit):
        card = ctk.CTkFrame(self.main_container, fg_color="gray20", corner_radius=10)
        card.pack(fill="x", pady=10)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        header.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        color_indicator = ctk.CTkFrame(
            title_frame, width=8, height=40, fg_color=habit["color"], corner_radius=4
        )
        color_indicator.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            title_frame, text=habit["name"],
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        if habit["description"]:
            ctk.CTkLabel(
                title_frame, text=f"  — {habit['description']}",
                font=ctk.CTkFont(size=14), text_color="gray"
            ).pack(side="left")

        action_frame = ctk.CTkFrame(header, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(
            action_frame, text="✏️", width=40, fg_color="gray",
            command=lambda hid=habit["id"]: self._show_edit_dialog(hid)
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            action_frame, text="🗑", width=40, fg_color="#e74c3c",
            command=lambda hid=habit["id"]: self._delete_habit(hid)
        ).pack(side="left", padx=3)

        stats = ctk.CTkFrame(card, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", padx=15, pady=5)

        current_streak = self.db.get_current_streak(habit["id"])
        best_streak = self.db.get_best_streak(habit["id"])
        total = self.db.get_total_completed(habit["id"])
        rate = self.db.get_completion_rate(habit["id"], 30)

        stats_data = [
            ("🔥 Текущая серия", f"{current_streak} дн."),
            ("🏆 Лучшая серия", f"{best_streak} дн."),
            ("✅ Всего выполнено", f"{total}"),
            ("📊 За 30 дней", f"{rate:.0f}%"),
        ]

        for i, (label, value) in enumerate(stats_data):
            cell = ctk.CTkFrame(stats, fg_color="gray15", corner_radius=8)
            cell.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            stats.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, pady=(8, 2))
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=18, weight="bold")).pack(padx=10, pady=(0, 8))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        bottom.grid_columnconfigure(0, weight=1)

        today = datetime.now().strftime("%Y-%m-%d")
        today_log = self.db.get_log(habit["id"], today)

        mark_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        mark_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ctk.CTkLabel(mark_frame, text="Отметка за сегодня:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 10))

        if today_log:
            status_text = "✅ Выполнено" if today_log["status"] == "completed" else "⏭ Пропущено"
            ctk.CTkLabel(mark_frame, text=status_text, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
            ctk.CTkButton(
                mark_frame, text="Изменить", width=100, fg_color="gray",
                command=lambda hid=habit["id"]: self._toggle_today(hid)
            ).pack(side="left", padx=10)
        else:
            ctk.CTkButton(
                mark_frame, text="✅ Выполнено", width=110, fg_color="#2ecc71",
                command=lambda hid=habit["id"]: self._mark(hid, "completed")
            ).pack(side="left", padx=5)
            ctk.CTkButton(
                mark_frame, text="⏭ Пропустить", width=110, fg_color="#95a5a6",
                command=lambda hid=habit["id"]: self._mark(hid, "skipped")
            ).pack(side="left", padx=5)

        heatmap_frame = ctk.CTkFrame(bottom, fg_color="gray15", corner_radius=8)
        heatmap_frame.grid(row=1, column=0, sticky="ew", pady=5)

        self._draw_heatmap(heatmap_frame, habit["id"])

    def _draw_heatmap(self, parent, habit_id):
        for widget in parent.winfo_children():
            widget.destroy()

        days = 35
        logs = self.db.get_logs_for_habit(habit_id, days)
        log_map = {log["date"]: log["status"] for log in logs}

        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, day in enumerate(weekdays):
            ctk.CTkLabel(parent, text=day, font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=i, padx=2,
                                                                                              pady=2)

        today = datetime.now().date()
        cells = []
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            status = log_map.get(date_str)

            if status == "completed":
                color = "#2ecc71"
            elif status == "skipped":
                color = "#e74c3c"
            else:
                color = "gray30"

            cell = ctk.CTkFrame(parent, width=28, height=28, fg_color=color, corner_radius=3)
            row = ((days - 1 - i) % 7) + 1
            col = (days - 1 - i) // 7
            cell.grid(row=row, column=col, padx=2, pady=2)

            cell.bind("<Enter>", lambda e, d=date_str, s=status: self._show_tooltip(d, s))

    def _show_tooltip(self, date_str, status):
        status_text = {"completed": "Выполнено", "skipped": "Пропущено", None: "Нет отметки"}
        self.configure(cursor="hand2")

    def _mark(self, habit_id, status):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            self.db.mark_habit(habit_id, today, status)
            self.refresh()
        except ValueError as e:
            messagebox.showwarning("Внимание", str(e))

    def _toggle_today(self, habit_id):
        today = datetime.now().strftime("%Y-%m-%d")
        log = self.db.get_log(habit_id, today)
        new_status = "skipped" if log["status"] == "completed" else "completed"
        self.db.update_habit_status(habit_id, today, new_status)
        self.refresh()

    def _delete_habit(self, habit_id):
        if messagebox.askyesno("Удаление", "Удалить привычку и всю историю?"):
            self.db.delete_habit(habit_id)
            self.refresh()

    def _show_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Новая привычка")
        dialog.geometry("400x300")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Название:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(20, 5), anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=360)
        name_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Описание (необязательно):", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5),
                                                                                               anchor="w")
        desc_entry = ctk.CTkEntry(dialog, width=360)
        desc_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Цвет:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        color_var = ctk.StringVar(value="#3498db")
        color_combo = ctk.CTkComboBox(dialog, values=["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"],
                                      variable=color_var, width=360)
        color_combo.pack(padx=20)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите название")
                return
            self.db.add_habit(name, desc_entry.get().strip(), color_var.get())
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Создать", command=save, width=360).pack(padx=20, pady=20)

    def _show_edit_dialog(self, habit_id):
        habit = self.db.get_habit(habit_id)
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактировать привычку")
        dialog.geometry("400x300")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Название:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(20, 5), anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=360)
        name_entry.insert(0, habit["name"])
        name_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Описание:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        desc_entry = ctk.CTkEntry(dialog, width=360)
        desc_entry.insert(0, habit["description"] or "")
        desc_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Цвет:", font=ctk.CTkFont(size=14)).pack(padx=20, pady=(15, 5), anchor="w")
        color_var = ctk.StringVar(value=habit["color"])
        color_combo = ctk.CTkComboBox(dialog, values=["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"],
                                      variable=color_var, width=360)
        color_combo.pack(padx=20)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите название")
                return
            self.db.update_habit(habit_id, name, desc_entry.get().strip(), color_var.get())
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Сохранить", command=save, width=360).pack(padx=20, pady=20)

    def _export(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Экспорт данных привычек"
        )
        if filepath:
            count = self.db.export_data(filepath)
            messagebox.showinfo("Экспорт", f"Экспортировано привычек: {count}")

    def _import(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Импорт данных привычек"
        )
        if filepath:
            try:
                count = self.db.import_data(filepath)
                messagebox.showinfo("Импорт", f"Импортировано привычек: {count}")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать: {e}")

    def destroy(self):
        self.db.close()
        super().destroy()