import customtkinter as ctk
from utils.currency_tracker import CurrencyTrackerFrame
from utils.budget_manager import BudgetManagerFrame
from utils.habit_tracker import HabitTrackerFrame
from utils.schedule_manager import ScheduleManagerFrame


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SuperApp v1.3")

        self.minsize(1000, 700)

        self.geometry("1200x800")

        self.resizable(True, True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)  # ← Было 7, стало 5
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="SUPER APP",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)

        ctk.CTkButton(
            self.sidebar, text="💱 Курсы валют", height=40,
            command=lambda: self.show_frame("currency")
        ).grid(row=1, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkButton(
            self.sidebar, text="💰 Бюджет и накопления", height=40,
            command=lambda: self.show_frame("budget")
        ).grid(row=2, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkButton(
            self.sidebar, text="🎯 Трекер привычек", height=40,
            command=lambda: self.show_frame("habits")
        ).grid(row=3, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkButton(
            self.sidebar, text="📅 Расписание", height=40,
            command=lambda: self.show_frame("schedule")
        ).grid(row=4, column=0, padx=20, pady=6, sticky="ew")

        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.show_frame("currency")

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_remove()

        if frame_name not in self.frames:
            if frame_name == "currency":
                self.frames[frame_name] = CurrencyTrackerFrame(self.main_area)
            elif frame_name == "budget":
                self.frames[frame_name] = BudgetManagerFrame(self.main_area)
            elif frame_name == "habits":
                self.frames[frame_name] = HabitTrackerFrame(self.main_area)
            elif frame_name == "schedule":
                self.frames[frame_name] = ScheduleManagerFrame(self.main_area)

        self.frames[frame_name].grid(row=0, column=0, sticky="nsew", padx=20, pady=20)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()