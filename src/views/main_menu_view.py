import customtkinter as ctk
class MainMenuView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        self.title_label = ctk.CTkLabel(center_frame, text="Menu Principal", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(0, 40))
        self.buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        self.buttons_frame.pack()
        self.admin_button = ctk.CTkButton(self.buttons_frame, text="Dashboard de Gestão", command=lambda: self.controller.show_frame("AdminDashboardView"), height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#1F6AA5")
        self.partner_button = ctk.CTkButton(self.buttons_frame, text="Registrar Ocorrência de Chamada (Detalhado)", command=lambda: self.controller.show_frame("RegistrationView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_call_button = ctk.CTkButton(self.buttons_frame, text="Registrar Ocorrência de Chamada (Simplificado)", command=lambda: self.controller.show_frame("SimpleCallView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_equip_button = ctk.CTkButton(self.buttons_frame, text="Registrar Suporte Técnico de Equipamento", command=lambda: self.controller.show_frame("EquipmentView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.history_button = ctk.CTkButton(self.buttons_frame, text="Ver Meu Histórico de Ocorrências", command=lambda: self.controller.show_frame("HistoryView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.history_button.pack(pady=8, padx=20, fill="x")
        self.logout_button = ctk.CTkButton(self.buttons_frame, text="Logout (Trocar de usuário)", command=self.controller.perform_logout, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#D32F2F", hover_color="#B71C1C")
        self.logout_button.pack(pady=(20, 8), padx=20, fill="x")
        self.exit_button = ctk.CTkButton(self.buttons_frame, text="Fechar Aplicação", command=self.controller.quit, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="gray50", hover_color="gray40")
        self.exit_button.pack(pady=8, padx=20, fill="x")
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="bottom", fill="x", pady=10, padx=20)
    def update_user_info(self, email, username):
        welcome_name = username if username else email
        self.title_label.configure(text=f"Bem-vindo, {welcome_name}!")
        self.status_label.configure(text=f"Login como: {email}")
    def update_buttons(self, role):
        for widget in (self.admin_button, self.partner_button, self.prefeitura_call_button, self.prefeitura_equip_button): widget.pack_forget()
        if role == "admin": self.admin_button.pack(pady=8, padx=20, fill="x", before=self.history_button)
        elif role == "partner": self.partner_button.pack(pady=8, padx=20, fill="x", before=self.history_button)
        elif role == "prefeitura":
            self.prefeitura_call_button.pack(pady=8, padx=20, fill="x", before=self.history_button)
            self.prefeitura_equip_button.pack(pady=8, padx=20, fill="x", before=self.history_button)
