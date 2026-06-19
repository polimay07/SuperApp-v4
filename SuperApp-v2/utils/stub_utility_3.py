import customtkinter as ctk


class StubUtility3Frame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        icon_label = ctk.CTkLabel(
            center_frame,
            text="⚙️",
            font=ctk.CTkFont(size=64)
        )
        icon_label.pack(pady=(0, 20))

        title_label = ctk.CTkLabel(
            center_frame,
            text="Менеджер задач",
            font=ctk.CTkFont(size=24, weight="bold"),
            wraplength=400,
            justify="center"
        )
        title_label.pack(pady=(0, 10))

        status_label = ctk.CTkLabel(
            center_frame,
            text="(В разработке)",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        status_label.pack(pady=(10, 0))