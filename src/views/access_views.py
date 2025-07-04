import customtkinter as ctk

class RequestAccessView(ctk.CTkFrame):
    """Tela para utilizadores não registados solicitarem acesso."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registado. Por favor, preencha os seus dados para solicitar o acesso.", wraplength=400)
        subtitle.pack(pady=(0, 20))

        ctk.CTkLabel(center_frame, text="Nome Completo:").pack(anchor="w", padx=20)
        self.name_entry = ctk.CTkEntry(center_frame, placeholder_text="Digite o seu nome completo", width=300)
        self.name_entry.pack(pady=(0,10), padx=20, fill="x")

        ctk.CTkLabel(center_frame, text="Nome de Utilizador:").pack(anchor="w", padx=20)
        self.username_entry = ctk.CTkEntry(center_frame, placeholder_text="Ex: jsilva", width=300)
        self.username_entry.pack(pady=(0,10), padx=20, fill="x")

        ctk.CTkLabel(center_frame, text="Selecione o seu vínculo:").pack(anchor="w", padx=20)
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Parceiro 67 Telecom", "Prefeitura de Ponta Porã"], width=300)
        self.role_combobox.pack(pady=(0,20), padx=20, fill="x")
        self.role_combobox.set("Parceiro 67 Telecom")

        submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40)
        submit_button.pack(pady=10, padx=20, fill="x")
        
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, fg_color="gray50")
        logout_button.pack(pady=10, padx=20, fill="x")
    
    def on_show(self):
        """Limpa os campos quando a tela é mostrada."""
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Parceiro 67 Telecom")

    def submit(self):
        """Passa a solicitação para o controlador."""
        full_name = self.name_entry.get()
        username = self.username_entry.get()
        role = self.role_combobox.get()
        self.controller.submit_access_request(full_name, username, role)


class PendingApprovalView(ctk.CTkFrame):
    """Tela mostrada a utilizadores que aguardam aprovação."""
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