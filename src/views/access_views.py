# ==============================================================================
# FICHEIRO: src/views/access_views.py
# DESCRIÇÃO: Contém as classes de interface para o fluxo de solicitação
#            e aprovação de acesso de novos utilizadores.
#            (VERSÃO COM VALIDAÇÕES E CORES MELHORADAS)
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import re # Importação adicionada para validações com regex

class RequestAccessView(ctk.CTkFrame):
    """Tela para novos usuários solicitarem acesso ao sistema."""
    def __init__(self, parent, controller):
        super().__init__(parent) # Removido fg_color do super().__init__
        self.controller = controller
        
        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        # --- Listas de Opções ---
        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        # Departamentos genéricos da Prefeitura
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        # --- Configuração da Responsividade ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)
        
        # --- Widgets da Interface (Criação) ---
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.",
                                wraplength=400, text_color="gray70")
        
        # Nome Completo
        name_label = ctk.CTkLabel(center_frame, text="Nome Completo:", text_color=self.controller.TEXT_COLOR)
        self.name_entry = ctk.CTkEntry(center_frame, placeholder_text="Digite seu nome completo", width=300,
                                       fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                       border_color="gray40")
        self.name_error_label = ctk.CTkLabel(center_frame, text="", text_color="red", font=ctk.CTkFont(size=11))

        # Nome de Usuário
        username_label = ctk.CTkLabel(center_frame, text="Nome de Usuário:", text_color=self.controller.TEXT_COLOR)
        self.username_entry = ctk.CTkEntry(center_frame, placeholder_text="Ex: jsilva", width=300,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.username_error_label = ctk.CTkLabel(center_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        
        # Vínculo Principal (Role)
        role_label = ctk.CTkLabel(center_frame, text="Selecione seu Vínculo Principal:", text_color=self.controller.TEXT_COLOR)
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected,
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        
        # Departamento/Empresa (Condicional)
        self.company_name_label = ctk.CTkLabel(center_frame, text="Selecione o Departamento/Empresa:", text_color=self.controller.TEXT_COLOR)
        self.company_name_combobox = ctk.CTkComboBox(center_frame, values=[], width=300,
                                                     fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                     border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                     button_hover_color=self.controller.ACCENT_COLOR)
        self.company_error_label = ctk.CTkLabel(center_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        
        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40,
                                           fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                           fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)

        # --- Posicionamento dos Widgets (Packing) ---
        title.pack(pady=(0,10))
        subtitle.pack(pady=(0, 20))
        
        name_label.pack(anchor="w", padx=20)
        self.name_entry.pack(pady=(0,2), padx=20, fill="x")
        self.name_error_label.pack(anchor="w", padx=20, pady=(0,8)) # Mensagem de erro para nome
        
        username_label.pack(anchor="w", padx=20)
        self.username_entry.pack(pady=(0,2), padx=20, fill="x")
        self.username_error_label.pack(anchor="w", padx=20, pady=(0,8)) # Mensagem de erro para username
        
        role_label.pack(anchor="w", padx=20)
        self.role_combobox.pack(pady=(0,10), padx=20, fill="x")
        
        # Widgets condicionais são posicionados e configurados pela função _on_role_selected
        self.company_name_label.pack(anchor="w", padx=20)
        self.company_name_combobox.pack(pady=(0,2), padx=20, fill="x")
        self.company_error_label.pack(anchor="w", padx=20, pady=(0,8)) # Mensagem de erro para company
        
        self.submit_button.pack(pady=20, padx=20, fill="x")
        self.logout_button.pack(pady=10, padx=20, fill="x")

        # --- Configuração da Lógica de Validação Proativa ---
        self.default_border_color = self.name_entry.cget("border_color")
        self.name_entry.bind("<KeyRelease>", self._validate_name_live)
        self.name_entry.bind("<FocusOut>", self._validate_name_live)

        self.username_entry.bind("<KeyRelease>", self._validate_username_live)
        self.username_entry.bind("<FocusOut>", self._validate_username_live)
        
        self.company_name_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.role_combobox.bind("<<ComboboxSelected>>", self._validate_company_live) # Para revalidar ao mudar o tipo de vínculo

        # Define o estado inicial da UI
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback() # Reseta o feedback visual no início

    def _reset_validation_feedback(self):
        """Reseta as cores das bordas e as mensagens de erro."""
        self.name_entry.configure(border_color=self.default_border_color)
        self.name_error_label.configure(text="")
        self.username_entry.configure(border_color=self.default_border_color)
        self.username_error_label.configure(text="")
        self.company_name_combobox.configure(border_color=self.default_border_color)
        self.company_error_label.configure(text="")

    def _validate_name_live(self, event=None):
        """Valida o campo Nome Completo em tempo real."""
        name = self.name_entry.get().strip()
        is_valid = bool(name)
        if is_valid:
            self.name_entry.configure(border_color=self.default_border_color)
            self.name_error_label.configure(text="")
        else:
            self.name_entry.configure(border_color="red")
            self.name_error_label.configure(text="O nome completo é obrigatório.")
        return is_valid

    def _validate_username_live(self, event=None):
        """Valida o formato do nome de utilizador em tempo real."""
        username = self.username_entry.get()
        is_valid = True
        message = ""

        if not username.strip():
            is_valid = False
            message = "O nome de utilizador é obrigatório."
        elif not (4 <= len(username) <= 16):
            is_valid = False
            message = "Deve ter entre 4 e 16 caracteres."
        elif not re.fullmatch(r"^[a-zA-Z0-9_.]*$", username): # Permite letras, números, _ e .
            is_valid = False
            message = "Não pode conter espaços ou caracteres especiais (exceto _ e .)."

        if is_valid:
            self.username_entry.configure(border_color=self.default_border_color)
            self.username_error_label.configure(text="")
        else:
            self.username_entry.configure(border_color="red")
            self.username_error_label.configure(text=f"Nome de utilizador inválido: {message}")
        
        return is_valid

    def _validate_company_live(self, event=None):
        """Valida o campo Departamento/Empresa em tempo real, se visível."""
        selected_role = self.role_combobox.get()
        # Mapeia o nome de exibição para o nome interno do grupo
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(selected_role)

        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_name_combobox.get().strip()
            is_valid = bool(company_name)
            if is_valid:
                self.company_name_combobox.configure(border_color=self.default_border_color)
                self.company_error_label.configure(text="")
            else:
                self.company_name_combobox.configure(border_color="red")
                self.company_error_label.configure(text="A seleção do departamento/empresa é obrigatória.")
            return is_valid
        return True # Se o campo não é visível, é sempre válido

    def _on_role_selected(self, selected_role):
        """Mostra ou esconde o campo de empresa/departamento com base no vínculo."""
        if selected_role == "Parceiro":
            self.company_name_label.pack(anchor="w", padx=20, before=self.submit_button)
            self.company_name_combobox.pack(pady=(0,2), padx=20, fill="x", before=self.submit_button)
            self.company_error_label.pack(anchor="w", padx=20, pady=(0,8), before=self.submit_button)
            
            self.company_name_label.configure(text="Selecione a Empresa Parceira:")
            self.company_name_combobox.configure(values=self.partner_list)
            self.company_name_combobox.set(self.partner_list[0] if self.partner_list else "")
            
        elif selected_role == "Prefeitura":
            self.company_name_label.pack(anchor="w", padx=20, before=self.submit_button)
            self.company_name_combobox.pack(pady=(0,2), padx=20, fill="x", before=self.submit_button)
            self.company_error_label.pack(anchor="w", padx=20, pady=(0,8), before=self.submit_button)
            
            self.company_name_label.configure(text="Selecione o Departamento:")
            self.company_name_combobox.configure(values=self.prefeitura_dept_list)
            self.company_name_combobox.set(self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")
            
        else: # Colaboradores 67
            self.company_name_label.pack_forget()
            self.company_name_combobox.pack_forget()
            self.company_error_label.pack_forget() # Esconde a mensagem de erro também

        # Revalidar o campo da empresa/departamento ao mudar o tipo de vínculo
        self._validate_company_live()


    def on_show(self):
        """Limpa os campos do formulário e reseta feedback visual sempre que a tela é exibida."""
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback() # Reseta o feedback visual

    def submit(self):
        """Coleta os dados do formulário e os envia para o controlador, com validação completa."""
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        # Mapeia o nome de exibição para o nome interno do grupo
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(self.role_combobox.get())
        
        company_name = None
        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_name_combobox.get()
        
        # Define o subgrupo padrão para novas solicitações
        sub_group = "USER"
        
        # --- Validações Finais Antes da Submissão ---
        all_valid = True
        
        if not self._validate_name_live():
            all_valid = False
        
        if not self._validate_username_live():
            all_valid = False

        if main_group in ["PARTNER", "PREFEITURA"] and not self._validate_company_live():
            all_valid = False
            
        if not all_valid:
            messagebox.showwarning("Campos Inválidos", "Por favor, corrija os campos destacados em vermelho antes de enviar a solicitação.")
            return

        self.controller.submit_access_request(full_name, username, main_group, sub_group, company_name)


class PendingApprovalView(ctk.CTkFrame):
    """Tela mostrada enquanto o acesso do usuário está pendente de aprovação."""
    def __init__(self, parent, controller):
        super().__init__(parent) # Removido fg_color do super().__init__
        self.controller = controller
        
        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        title = ctk.CTkLabel(center_frame, text="Acesso Pendente",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        
        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação de um administrador.",
                                wraplength=450, text_color="gray70")
        subtitle.pack(pady=(0, 20))
        
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                      fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        logout_button.pack()
