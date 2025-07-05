import customtkinter as ctk

class RequestAccessView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.", wraplength=400)
        subtitle.pack(pady=(0, 20))
        ctk.CTkLabel(center_frame, text="Nome Completo:").pack(anchor="w", padx=20)
        self.name_entry = ctk.CTkEntry(center_frame, placeholder_text="Digite seu nome completo", width=300)
        self.name_entry.pack(pady=(0,10), padx=20, fill="x")
        ctk.CTkLabel(center_frame, text="Nome de Usuário:").pack(anchor="w", padx=20)
        self.username_entry = ctk.CTkEntry(center_frame, placeholder_text="Ex: jsilva", width=300)
        self.username_entry.pack(pady=(0,10), padx=20, fill="x")
        ctk.CTkLabel(center_frame, text="Selecione seu vínculo:").pack(anchor="w", padx=20)
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Parceiro 67 Telecom", "Prefeitura de Ponta Porã"], width=300)
        self.role_combobox.pack(pady=(0,20), padx=20, fill="x")
        self.role_combobox.set("Parceiro 67 Telecom")
        submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40)
        submit_button.pack(pady=10, padx=20, fill="x")
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, fg_color="gray50")
        logout_button.pack(pady=10, padx=20, fill="x")
    
    def on_show(self):
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Parceiro 67 Telecom")

    def submit(self):
        self.controller.submit_access_request(self.name_entry.get(), self.username_entry.get(), self.role_combobox.get())

class PendingApprovalView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        title = ctk.CTkLabel(center_frame, text="Acesso Pendente", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação.", wraplength=450)
        subtitle.pack(pady=(0, 20))
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40)
        logout_button.pack()