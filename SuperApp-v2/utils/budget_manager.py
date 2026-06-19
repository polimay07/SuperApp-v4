import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data.budget_db import BudgetDB


class BudgetManagerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db = BudgetDB()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self, text="💰 Бюджет и накопления",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Навигация по вкладкам внутри утилиты
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)

        self.tab_overview = self.tabview.add("📊 Обзор")
        self.tab_add = self.tabview.add(" Операция")
        self.tab_categories = self.tabview.add("🏷 Категории")
        self.tab_goals = self.tabview.add("🎯 Цели")
        self.tab_analytics = self.tabview.add("📈 Аналитика")

        # Инициализация вкладок
        self._build_overview()
        self._build_add_tab()
        self._build_categories_tab()
        self._build_goals_tab()
        self._build_analytics_tab()

    # ============ ОБЗОР ============
    def _build_overview(self):
        self.tab_overview.grid_columnconfigure(0, weight=1)
        self.tab_overview.grid_rowconfigure(2, weight=1)

        # Баланс
        self.balance_label = ctk.CTkLabel(
            self.tab_overview, text="Баланс: 0 ₽",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.balance_label.grid(row=0, column=0, pady=20)

        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            self.tab_overview, text="🔄 Обновить",
            command=self.refresh_overview
        )
        refresh_btn.grid(row=0, column=1, padx=20, pady=20)

        # Заголовок списка
        ctk.CTkLabel(
            self.tab_overview, text="Последние 10 операций:",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=10)

        # Список транзакций
        self.tx_frame = ctk.CTkScrollableFrame(self.tab_overview, height=300)
        self.tx_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.tx_frame.grid_columnconfigure(0, weight=1)

        self.refresh_overview()

    def refresh_overview(self):
        balance = self.db.get_balance()
        color = "#2ecc71" if balance >= 0 else "#e74c3c"
        self.balance_label.configure(text=f"Баланс: {balance:,.2f} ₽", text_color=color)

        # Очистка списка
        for widget in self.tx_frame.winfo_children():
            widget.destroy()

        transactions = self.db.get_recent_transactions(10)
        if not transactions:
            ctk.CTkLabel(self.tx_frame, text="Нет операций", text_color="gray").pack(pady=20)
            return

        for tx in transactions:
            row = ctk.CTkFrame(self.tx_frame, fg_color="gray20")
            row.pack(fill="x", pady=3, padx=5)

            sign = "+" if tx["type"] == "income" else "-"
            tx_color = "#2ecc71" if tx["type"] == "income" else "#e74c3c"
            cat = tx["category_name"] if tx["category_name"] else "Без категории"
            desc = f" — {tx['description']}" if tx["description"] else ""

            ctk.CTkLabel(row, text=tx["date"], width=140, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=cat, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{desc}", width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(
                row, text=f"{sign}{tx['amount']:,.2f} ₽",
                text_color=tx_color, font=ctk.CTkFont(weight="bold")
            ).pack(side="right", padx=10)

    # ============ ДОБАВИТЬ ОПЕРАЦИЮ ============
    def _build_add_tab(self):
        self.tab_add.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.tab_add, text="Тип:", font=ctk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.type_var = ctk.StringVar(value="expense")
        type_frame = ctk.CTkFrame(self.tab_add, fg_color="transparent")
        type_frame.grid(row=0, column=1, sticky="w")
        ctk.CTkRadioButton(type_frame, text="Расход", variable=self.type_var, value="expense", command=self._update_category_combo).pack(side="left", padx=5)
        ctk.CTkRadioButton(type_frame, text="Доход", variable=self.type_var, value="income", command=self._update_category_combo).pack(side="left", padx=5)

        ctk.CTkLabel(self.tab_add, text="Категория:", font=ctk.CTkFont(size=16)).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.category_var = ctk.StringVar()
        self.category_combo = ctk.CTkComboBox(self.tab_add, variable=self.category_var, width=300)
        self.category_combo.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        self._update_category_combo()

        ctk.CTkLabel(self.tab_add, text="Сумма (₽):", font=ctk.CTkFont(size=16)).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.amount_entry = ctk.CTkEntry(self.tab_add, placeholder_text="0.00", width=300)
        self.amount_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(self.tab_add, text="Описание:", font=ctk.CTkFont(size=16)).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.desc_entry = ctk.CTkEntry(self.tab_add, placeholder_text="Комментарий...", width=300)
        self.desc_entry.grid(row=3, column=1, padx=20, pady=10, sticky="w")

        save_btn = ctk.CTkButton(
            self.tab_add, text="💾 Сохранить операцию",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._save_transaction
        )
        save_btn.grid(row=4, column=1, padx=20, pady=20, sticky="w")

        self.msg_label = ctk.CTkLabel(self.tab_add, text="")
        self.msg_label.grid(row=5, column=1, padx=20, sticky="w")

    def _update_category_combo(self):
        ctype = self.type_var.get()
        cats = self.db.get_categories(ctype)
        self.category_combo.configure(values=[c["name"] for c in cats])
        if cats:
            self.category_combo.set(cats[0]["name"])

    def _save_transaction(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError
            cat_name = self.category_var.get()
            cats = self.db.get_categories(self.type_var.get())
            cat_id = next((c["id"] for c in cats if c["name"] == cat_name), None)
            desc = self.desc_entry.get()

            self.db.add_transaction(self.type_var.get(), cat_id, amount, desc)
            self.msg_label.configure(text="✅ Операция сохранена!", text_color="#2ecc71")
            self.amount_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self.refresh_overview()
        except ValueError:
            self.msg_label.configure(text="❌ Введите корректную сумму", text_color="#e74c3c")

    # ============ КАТЕГОРИИ ============
    def _build_categories_tab(self):
        self.tab_categories.grid_columnconfigure(0, weight=1)
        self.tab_categories.grid_rowconfigure(2, weight=1)

        # Добавление
        ctk.CTkLabel(self.tab_categories, text="Новая категория:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        add_frame = ctk.CTkFrame(self.tab_categories, fg_color="transparent")
        add_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.new_cat_name = ctk.CTkEntry(add_frame, placeholder_text="Название (напр. 🎓 Учёба)", width=250)
        self.new_cat_name.pack(side="left", padx=5)

        self.new_cat_type = ctk.StringVar(value="expense")
        ctk.CTkRadioButton(add_frame, text="Расход", variable=self.new_cat_type, value="expense").pack(side="left", padx=5)
        ctk.CTkRadioButton(add_frame, text="Доход", variable=self.new_cat_type, value="income").pack(side="left", padx=5)

        add_btn = ctk.CTkButton(add_frame, text="Добавить", command=self._add_category)
        add_btn.pack(side="left", padx=10)

        # Список
        self.cat_frame = ctk.CTkScrollableFrame(self.tab_categories, height=300)
        self.cat_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.cat_frame.grid_columnconfigure(0, weight=1)

        self._refresh_categories()

    def _refresh_categories(self):
        for widget in self.cat_frame.winfo_children():
            widget.destroy()

        for ctype, title in [("income", " Доходы"), ("expense", " Расходы")]:
            ctk.CTkLabel(self.cat_frame, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(10, 5))
            cats = self.db.get_categories(ctype)
            for c in cats:
                row = ctk.CTkFrame(self.cat_frame, fg_color="gray20")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=c["name"]).pack(side="left", padx=10, pady=5)
                del_btn = ctk.CTkButton(
                    row, text="", width=40, fg_color="#e74c3c",
                    command=lambda cid=c["id"]: self._delete_category(cid)
                )
                del_btn.pack(side="right", padx=5, pady=5)

    def _add_category(self):
        name = self.new_cat_name.get().strip()
        if name:
            self.db.add_category(name, self.new_cat_type.get())
            self.new_cat_name.delete(0, "end")
            self._refresh_categories()
            self._update_category_combo()

    def _delete_category(self, cat_id):
        self.db.delete_category(cat_id)
        self._refresh_categories()
        self._update_category_combo()

    # ============ ЦЕЛИ ============
    def _build_goals_tab(self):
        self.tab_goals.grid_columnconfigure(0, weight=1)
        self.tab_goals.grid_rowconfigure(2, weight=1)

        # Форма добавления
        ctk.CTkLabel(self.tab_goals, text="Новая цель:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        add_frame = ctk.CTkFrame(self.tab_goals, fg_color="transparent")
        add_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.goal_name = ctk.CTkEntry(add_frame, placeholder_text="Название цели", width=180)
        self.goal_name.pack(side="left", padx=5)
        self.goal_target = ctk.CTkEntry(add_frame, placeholder_text="Сумма ₽", width=120)
        self.goal_target.pack(side="left", padx=5)
        self.goal_deadline = ctk.CTkEntry(add_frame, placeholder_text="Дедлайн (ГГГГ-ММ-ДД)", width=150)
        self.goal_deadline.pack(side="left", padx=5)

        add_btn = ctk.CTkButton(add_frame, text="Создать цель", command=self._add_goal)
        add_btn.pack(side="left", padx=10)

        # Список целей
        self.goals_frame = ctk.CTkScrollableFrame(self.tab_goals, height=300)
        self.goals_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.goals_frame.grid_columnconfigure(0, weight=1)

        self._refresh_goals()

    def _refresh_goals(self):
        for widget in self.goals_frame.winfo_children():
            widget.destroy()

        goals = self.db.get_goals()
        if not goals:
            ctk.CTkLabel(self.goals_frame, text="Нет целей. Создайте первую!", text_color="gray").pack(pady=30)
            return

        for g in goals:
            row = ctk.CTkFrame(self.goals_frame, fg_color="gray20")
            row.pack(fill="x", pady=5)

            progress = min(100, (g["current_amount"] / g["target_amount"]) * 100) if g["target_amount"] > 0 else 0

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=10)

            ctk.CTkLabel(info, text=f"🎯 {g['name']}", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"{g['current_amount']:,.0f} / {g['target_amount']:,.0f} ₽ ({progress:.0f}%)", anchor="w").pack(fill="x")

            bar = ctk.CTkProgressBar(info, width=200)
            bar.pack(fill="x", pady=5)
            bar.set(progress / 100)

            controls = ctk.CTkFrame(row, fg_color="transparent")
            controls.pack(side="right", padx=10)

            add_amount = ctk.CTkEntry(controls, placeholder_text="+сумма", width=80)
            add_amount.pack(pady=3)

            ctk.CTkButton(
                controls, text="Пополнить", width=90,
                command=lambda gid=g["id"], entry=add_amount: self._top_up_goal(gid, entry)
            ).pack(pady=3)

            ctk.CTkButton(
                controls, text="🗑 Удалить", width=90, fg_color="#e74c3c",
                command=lambda gid=g["id"]: self._delete_goal(gid)
            ).pack(pady=3)

    def _add_goal(self):
        name = self.goal_name.get().strip()
        try:
            target = float(self.goal_target.get())
            deadline = self.goal_deadline.get().strip() or None
            if name and target > 0:
                self.db.add_goal(name, target, deadline)
                self.goal_name.delete(0, "end")
                self.goal_target.delete(0, "end")
                self.goal_deadline.delete(0, "end")
                self._refresh_goals()
        except ValueError:
            pass

    def _top_up_goal(self, goal_id, entry):
        try:
            amount = float(entry.get())
            goals = self.db.get_goals()
            goal = next((g for g in goals if g["id"] == goal_id), None)
            if goal:
                new_amount = goal["current_amount"] + amount
                self.db.update_goal_amount(goal_id, new_amount)
                entry.delete(0, "end")
                self._refresh_goals()
        except ValueError:
            pass

    def _delete_goal(self, goal_id):
        self.db.delete_goal(goal_id)
        self._refresh_goals()

    # ============ АНАЛИТИКА ============
    def _build_analytics_tab(self):
        self.tab_analytics.grid_columnconfigure(0, weight=1)
        self.tab_analytics.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.tab_analytics, text="Расходы по категориям за текущий месяц",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=15)

        self.chart_frame = ctk.CTkFrame(self.tab_analytics)
        self.chart_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        self.refresh_analytics()

    def refresh_analytics(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        data = self.db.get_month_expenses_by_category()

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)

        if not data:
            ax.text(0.5, 0.5, "Нет расходов в этом месяце",
                    ha='center', va='center', fontsize=14, color='gray')
            ax.axis('off')
        else:
            labels = [row["name"] for row in data]
            sizes = [row["total"] for row in data]
            colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%',
                colors=colors[:len(labels)], startangle=140,
                textprops={'color': 'white', 'fontsize': 10}
            )
            for t in autotexts:
                t.set_fontsize(11)
                t.set_fontweight('bold')
            ax.set_title("Структура расходов", fontsize=14, pad=20, color='white')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def destroy(self):
        self.db.close()
        super().destroy()