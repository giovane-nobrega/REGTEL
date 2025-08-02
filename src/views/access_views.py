# ==============================================================================
# FICHEIRO: src/views/access_views.py
# DESCRIÇÃO: Contém as classes de interface para o fluxo de solicitação
#            e aprovação de acesso de novos utilizadores. (VERSÃO CORRIGIDA)
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox

class RequestAccessView(ctk.CTkFrame):
    """Tela para novos usuários solicitarem acesso ao sistema."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- Listas de Opções ---
        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        # --- Configuração da Responsividade ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)
        
        # --- Widgets da Interface ---
        # Todos os widgets são criados primeiro
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso", font=ctk.CTkFont(size=24, weight="bold"))
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.", wraplength=400)
        
        name_label = ctk.CTkLabel(center_frame, text="Nome Completo:")
        self.name_entry = ctk.CTkEntry(center_frame, placeholder_text="Digite seu nome completo", width=300)
        
        username_label = ctk.CTkLabel(center_frame, text="Nome de Usuário:")
        self.username_entry = ctk.CTkEntry(center_frame, placeholder_text="Ex: jsilva", width=300)
        
        role_label = ctk.CTkLabel(center_frame, text="Selecione seu Vínculo Principal:")
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected)
        
        self.company_name_label = ctk.CTkLabel(center_frame, text="Selecione o Departamento/Empresa:")
        self.company_name_combobox = ctk.CTkComboBox(center_frame, values=[], width=300)
        
        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40)
        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, fg_color="gray50")

        # --- Posicionamento dos Widgets (Packing) ---
        # A ordem do .pack() define a ordem visual
        title.pack(pady=(0,10))
        subtitle.pack(pady=(0, 20))
        name_label.pack(anchor="w", padx=20)
        self.name_entry.pack(pady=(0,10), padx=20, fill="x")
        username_label.pack(anchor="w", padx=20)
        self.username_entry.pack(pady=(0,10), padx=20, fill="x")
        role_label.pack(anchor="w", padx=20)
        self.role_combobox.pack(pady=(0,10), padx=20, fill="x")
        
        # Os widgets condicionais são posicionados pela função _on_role_selected
        self.company_name_label.pack(anchor="w", padx=20)
        self.company_name_combobox.pack(pady=(0,10), padx=20, fill="x")
        
        self.submit_button.pack(pady=20, padx=20, fill="x")
        self.logout_button.pack(pady=10, padx=20, fill="x")

        # Define o estado inicial da UI
        self._on_role_selected("Prefeitura")

    def _on_role_selected(self, selected_role):
        """Mostra ou esconde o campo de empresa/departamento com base no vínculo."""
        if selected_role == "Parceiro":
            # Re-empacota os widgets se eles já foram escondidos
            self.company_name_label.pack(anchor="w", padx=20, before=self.submit_button)
            self.company_name_combobox.pack(pady=(0,10), padx=20, fill="x", before=self.submit_button)
            
            self.company_name_label.configure(text="Selecione a Empresa Parceira:")
            self.company_name_combobox.configure(values=self.partner_list)
            self.company_name_combobox.set(self.partner_list[0])
            
        elif selected_role == "Prefeitura":
            # Re-empacota os widgets se eles já foram escondidos
            self.company_name_label.pack(anchor="w", padx=20, before=self.submit_button)
            self.company_name_combobox.pack(pady=(0,10), padx=20, fill="x", before=self.submit_button)
            
            self.company_name_label.configure(text="Selecione o Departamento:")
            self.company_name_combobox.configure(values=self.prefeitura_dept_list)
            self.company_name_combobox.set(self.prefeitura_dept_list[0])
            
        else: # Colaboradores 67
            # Usa pack_forget() para esconder os widgets sem os destruir
            self.company_name_label.pack_forget()
            self.company_name_combobox.pack_forget()

    def on_show(self):
        """Limpa os campos do formulário sempre que a tela é exibida."""
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")

    def submit(self):
        """Coleta os dados do formulário e os envia para o controlador."""
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        # Mapeia o nome de exibição para o nome interno do grupo
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(self.role_combobox.get())
        
        company_name = None
        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_name_combobox.get()
            if not company_name:
                messagebox.showwarning("Campo Obrigatório", "A seleção do departamento/empresa é obrigatória.")
                return
        
        # Define o subgrupo padrão para novas solicitações
        sub_group = "USER"
        
        self.controller.submit_access_request(full_name, username, main_group, sub_group, company_name)


class PendingApprovalView(ctk.CTkFrame):
    """Tela mostrada enquanto o acesso do usuário está pendente de aprovação."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        title = ctk.CTkLabel(center_frame, text="Acesso Pendente", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0,10))
        
        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação de um administrador.", wraplength=450)
        subtitle.pack(pady=(0, 20))
        
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40)
        logout_button.pack()
