import customtkinter as ctk
class RequestAccessView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registado. Por favor, solicite o acesso.", wraplength=400)
        subtitle.pack(pady=(0, 20))
        ctk.CTkLabel(center_frame, text="Selecione o seu vínculo:").pack()
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Parceiro 67 Telecom", "Prefeitura de Ponta Porã"], width=250)
        self.role_combobox.pack(pady=(0,20))
        self.role_combobox.set("Parceiro 67 Telecom")
        submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40)
        submit_button.pack(pady=10)
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, fg_color="gray50")
        logout_button.pack()
    def submit(self): self.controller.submit_access_request(self.role_combobox.get())
class PendingApprovalView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        title = ctk.CTkLabel(center_frame, text="Acesso Pendente", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        subtitle = ctk.CTkLabel(center_frame, text="A sua solicitação de acesso está a aguardar aprovação.", wraplength=450)
        subtitle.pack(pady=(0, 20))
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40)
        logout_button.pack()