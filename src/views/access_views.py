import customtkinter as ctk
from tkinter import messagebox

class RequestAccessView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- Configuração da Responsividade ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)
        
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
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Prefeitura", "Parceiro"], width=300, command=self._on_role_selected)
        self.role_combobox.pack(pady=(0,10), padx=20, fill="x")
        self.role_combobox.set("Prefeitura")

        self.company_name_label = ctk.CTkLabel(center_frame, text="Selecione a Empresa Parceira:")
        company_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]
        self.company_name_combobox = ctk.CTkComboBox(center_frame, values=company_list, width=300)
        
        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40)
        self.submit_button.pack(pady=20, padx=20, fill="x")
        
        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, fg_color="gray50")
        self.logout_button.pack(pady=10, padx=20, fill="x")

        self._on_role_selected(self.role_combobox.get())

    def _on_role_selected(self, selected_role):
        if selected_role == "Parceiro":
            self.company_name_label.pack(anchor="w", padx=20, before=self.submit_button)
            self.company_name_combobox.pack(pady=(0,10), padx=20, fill="x", before=self.submit_button)
        else:
            self.company_name_label.pack_forget()
            self.company_name_combobox.pack_forget()

    def on_show(self):
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self.company_name_combobox.set("")
        self._on_role_selected("Prefeitura")

    def submit(self):
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        role = self.role_combobox.get()
        
        company_name = None
        if role == "Parceiro":
            company_name = self.company_name_combobox.get()
            if not company_name or company_name not in ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]:
                messagebox.showwarning("Campo Obrigatório", "A seleção da empresa parceira é obrigatória.")
                return

        self.controller.submit_access_request(full_name, username, role, company_name)

class PendingApprovalView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        title = ctk.CTkLabel(center_frame, text="Acesso Pendente", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação.", wraplength=450)
        subtitle.pack(pady=(0, 20))
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40)
        logout_button.pack()
