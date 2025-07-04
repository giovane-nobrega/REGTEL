import customtkinter as ctk
class MainMenuView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        title_label = ctk.CTkLabel(center_frame, text="Menu Principal", font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(0, 40))
        self.buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        self.buttons_frame.pack()
        self.admin_button = ctk.CTkButton(self.buttons_frame, text="Dashboard de Gestão", command=lambda: self.controller.show_frame("AdminDashboardView"), height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#1F6AA5")
        self.partner_button = ctk.CTkButton(self.buttons_frame, text="Registar Ocorrência de Chamada (Detalhado)", command=lambda: self.controller.show_frame("RegistrationView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_call_button = ctk.CTkButton(self.buttons_frame, text="Registar Ocorrência de Chamada (Simplificado)", command=lambda: self.controller.show_frame("SimpleCallView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_equip_button = ctk.CTkButton(self.buttons_frame, text="Registar Suporte Técnico de Equipamento", command=lambda: self.controller.show_frame("EquipmentView"), height=45, width=350, font=ctk.CTkFont(size=14))
        history_button = ctk.CTkButton(self.buttons_frame, text="Ver o Meu Histórico de Ocorrências", command=lambda: self.controller.show_frame("HistoryView"), height=45, width=350, font=ctk.CTkFont(size=14))
        history_button.pack(pady=8, padx=20, fill="x")
        logout_button = ctk.CTkButton(self.buttons_frame, text="Logout (Trocar de utilizador)", command=self.controller.perform_logout, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#D32F2F", hover_color="#B71C1C")
        logout_button.pack(pady=(20, 8), padx=20, fill="x")
        exit_button = ctk.CTkButton(self.buttons_frame, text="Fechar Aplicação", command=self.controller.quit, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="gray50", hover_color="gray40")
        exit_button.pack(pady=8, padx=20, fill="x")
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="bottom", fill="x", pady=10, padx=20)
    def update_user_info(self, email): self.status_label.configure(text=f"Login como: {email}")
    def update_buttons(self, role):
        for widget in (self.admin_button, self.partner_button, self.prefeitura_call_button, self.prefeitura_equip_button): widget.pack_forget()
        button_order = [self.winfo_children()[0].winfo_children()[1].winfo_children()[0]]
        if role == "admin": self.admin_button.pack(pady=8, padx=20, fill="x", before=button_order[0])
        elif role == "partner": self.partner_button.pack(pady=8, padx=20, fill="x", before=button_order[0])
        elif role == "prefeitura":
            self.prefeitura_call_button.pack(pady=8, padx=20, fill="x", before=button_order[0])
            self.prefeitura_equip_button.pack(pady=8, padx=20, fill="x", before=button_order[0])