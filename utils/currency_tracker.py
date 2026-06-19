import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data.cbr_client import CBRClient


class CurrencyTrackerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Заголовок
        self.title_label = ctk.CTkLabel(self, text="📈 Трекер курсов валют (ЦБ РФ)",
                                        font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)

        # Панель управления
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(pady=10, fill="x", padx=20)

        ctk.CTkLabel(self.control_frame, text="Выберите валюту:").pack(side="left", padx=10, pady=10)
        self.currency_var = ctk.StringVar(value="USD")
        self.currency_combo = ctk.CTkComboBox(self.control_frame, values=["USD", "EUR", "CNY", "GBP"],
                                              variable=self.currency_var, command=self.update_data)
        self.currency_combo.pack(side="left", padx=10, pady=10)

        self.refresh_btn = ctk.CTkButton(self.control_frame, text="Обновить данные", command=self.update_data)
        self.refresh_btn.pack(side="right", padx=10, pady=10)

        # Текстовая информация о текущем курсе
        self.info_label = ctk.CTkLabel(self, text="Загрузка данных...", font=ctk.CTkFont(size=16))
        self.info_label.pack(pady=10)

        # Область для графика
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Инициализация данных при запуске
        self.update_data()

    def update_data(self, *args):
        currency = self.currency_var.get()
        try:
            current_data = CBRClient.get_current_rates()
            valute_info = current_data.get(currency, {})
            current_rate = valute_info.get('Value', 0)
            previous_rate = valute_info.get('Previous', 0)
            diff = current_rate - previous_rate
            diff_str = f"{'🔺' if diff > 0 else '🔻'} {abs(diff):.4f}"

            self.info_label.configure(
                text=f"Текущий курс {currency}/RUB: {current_rate:.2f} руб. (Изменение: {diff_str})",
                text_color="#2ecc71" if diff > 0 else "#e74c3c"
            )

            df = CBRClient.get_historical_data(currency, days=30)

            self.draw_chart(df, currency)

        except Exception as e:
            self.info_label.configure(text=f"Ошибка загрузки данных: {e}", text_color="#e74c3c")
            print(f"❌ Ошибка: {e}")

    def draw_chart(self, df, currency):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        plt.style.use('dark_background')

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

        df['Дата_dt'] = pd.to_datetime(df['Дата'])

        ax.plot(df['Дата_dt'], df['Курс'], marker='o', color='#3498db', linewidth=2, markersize=5)

        tick_interval = max(1, len(df) // 6)
        tick_positions = df['Дата_dt'].iloc[::tick_interval]
        ax.set_xticks(tick_positions)

        ax.set_xticklabels([date.strftime('%d.%m') for date in tick_positions], rotation=45, ha='right')

        ax.set_title(f"Динамика курса {currency}/RUB за 30 дней", fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel("Дата", fontsize=11, labelpad=10)
        ax.set_ylabel("Курс (RUB)", fontsize=11, labelpad=10)

        ax.grid(True, linestyle='--', alpha=0.3)

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)