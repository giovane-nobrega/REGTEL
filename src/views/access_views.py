# ==============================================================================
# FICHEIRO: src/views/access_views.py
# DESCRIÇÃO: Contém as classes de interface para o fluxo de solicitação
#            e aprovação de acesso de novos utilizadores.
#            (VERSÃO COM VALIDAÇÕES E CORES MELHORADAS, GRUPAMENTO DE CAMPOS E FEEDBACK VISUAL)
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import re
import threading # Adicionado para verificação em segundo plano
import time      # Adicionado para pausas na verificação

class RequestAccessView(ctk.CTkFrame):
    """Tela para novos usuários solicitarem acesso ao sistema."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        # Adicionar "67 INTERNET" à lista de empresas parceiras
        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.",
                                wraplength=400, text_color="gray70")

        title.pack(pady=(0,10))
        subtitle.pack(pady=(0, 20))

        # --- FRAME PARA DADOS PESSOAIS ---
        personal_data_frame = ctk.CTkFrame(center_frame, fg_color="gray15", corner_radius=10)
        personal_data_frame.pack(pady=(10, 10), padx=20, fill="x", expand=False)
        personal_data_frame.grid_columnconfigure(0, weight=1) # Coluna para labels
        personal_data_frame.grid_columnconfigure(1, weight=3) # Coluna para entradas

        ctk.CTkLabel(personal_data_frame, text="Dados Pessoais", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # Nome Completo
        self.name_label = ctk.CTkLabel(personal_data_frame, text="Nome Completo:", text_color=self.controller.TEXT_COLOR)
        self.name_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5,0))
        self.name_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Digite seu nome completo", width=300,
                                       fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                       border_color="gray40")
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=15, pady=(5,0))
        self.name_validation_label = ctk.CTkLabel(personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.name_validation_label.grid(row=2, column=1, sticky="w", padx=15, pady=(0, 10))

        # Nome de Usuário
        self.username_label = ctk.CTkLabel(personal_data_frame, text="Nome de Usuário:", text_color=self.controller.TEXT_COLOR)
        self.username_label.grid(row=3, column=0, sticky="w", padx=15, pady=(5,0))
        self.username_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Ex: jsilva (4-16 caracteres, sem espaços)", width=300,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.username_entry.grid(row=3, column=1, sticky="ew", padx=15, pady=(5,0))
        self.username_validation_label = ctk.CTkLabel(personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.username_validation_label.grid(row=4, column=1, sticky="w", padx=15, pady=(0, 10))

        # --- FRAME PARA DADOS DE VÍNCULO ---
        affiliation_data_frame = ctk.CTkFrame(center_frame, fg_color="gray15", corner_radius=10)
        affiliation_data_frame.pack(pady=(10, 10), padx=20, fill="x", expand=False)
        affiliation_data_frame.grid_columnconfigure(0, weight=1) # Coluna para labels
        affiliation_data_frame.grid_columnconfigure(1, weight=3) # Coluna para entradas

        ctk.CTkLabel(affiliation_data_frame, text="Dados de Vínculo", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # Vínculo Principal (Role)
        self.role_label = ctk.CTkLabel(affiliation_data_frame, text="Vínculo Principal:", text_color=self.controller.TEXT_COLOR)
        self.role_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5,0))
        self.role_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected,
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        self.role_combobox.grid(row=1, column=1, sticky="ew", padx=15, pady=(5,10))

        # Departamento/Empresa (Condicional)
        self.company_label = ctk.CTkLabel(affiliation_data_frame, text="Departamento/Empresa:", text_color=self.controller.TEXT_COLOR)
        self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
        self.company_combobox = ctk.CTkComboBox(affiliation_data_frame, values=[], width=300,
                                                     fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                     border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                     button_hover_color=self.controller.ACCENT_COLOR)
        self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
        self.company_validation_label = ctk.CTkLabel(affiliation_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))

        # Novo combobox para subgrupo dentro de "Colaboradores 67"
        self.subgroup_67_label = ctk.CTkLabel(affiliation_data_frame, text="Selecione o Subgrupo:", text_color=self.controller.TEXT_COLOR)
        # Removido "USER", adicionado "67_TELECOM_USER" como a opção padrão para usuários 67 Telecom
        self.subgroup_67_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["67_TELECOM_USER", "67_INTERNET_USER"],
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                    button_hover_color=self.controller.ACCENT_COLOR)


        # --- Botões de Ação ---
        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40,
                                           fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        self.submit_button.pack(pady=20, padx=20, fill="x")

        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                           fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        self.logout_button.pack(pady=10, padx=20, fill="x")

        # --- Configuração da Lógica de Validação Proativa e Foco ---
        self.default_border_color = self.name_entry.cget("border_color")

        # Vincular validações e efeitos de foco
        self.name_entry.bind("<KeyRelease>", self._validate_name_live)
        self.name_entry.bind("<FocusOut>", self._validate_name_live)
        self.name_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.name_label))
        self.name_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.name_label))

        self.username_entry.bind("<KeyRelease>", self._validate_username_live)
        self.username_entry.bind("<FocusOut>", self._validate_username_live)
        self.username_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.username_label))
        self.username_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.username_label))

        self.company_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.role_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.company_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.company_label))
        self.company_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.company_label))
        self.role_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.role_label))
        self.role_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.role_label))

        self.subgroup_67_combobox.bind("<<ComboboxSelected>>", self._validate_company_live) # Revalida ao mudar subgrupo
        self.subgroup_67_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.subgroup_67_label))
        self.subgroup_67_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.subgroup_67_label))


        # Define o estado inicial da UI
        self.role_combobox.set("Prefeitura") # Define o valor inicial padrão
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()


    def _on_focus_in(self, label_widget):
        """Aplica estilo de foco (negrito) quando o widget associado recebe foco."""
        label_widget.configure(font=ctk.CTkFont(weight="bold", size=14)) # Aumenta um pouco e negrito

    def _on_focus_out(self, label_widget):
        """Remove estilo de foco (negrito) quando o widget associado perde foco."""
        label_widget.configure(font=ctk.CTkFont(weight="normal", size=13)) # Volta ao tamanho e peso normal

    def _reset_validation_feedback(self):
        """Reseta as cores das bordas e as mensagens de erro."""
        self.name_entry.configure(border_color=self.default_border_color)
        self.name_validation_label.configure(text="")

        self.username_entry.configure(border_color=self.default_border_color)
        self.username_validation_label.configure(text="")

        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")

    def _validate_name_live(self, event=None):
        """Valida o campo Nome Completo em tempo real e exibe feedback com ícone."""
        name = self.name_entry.get().strip()
        is_valid = bool(name)
        if is_valid:
            self.name_entry.configure(border_color=self.default_border_color)
            self.name_validation_label.configure(text="✔️ Nome válido", text_color="green")
        else:
            self.name_entry.configure(border_color="red")
            self.name_validation_label.configure(text="❌ O nome completo é obrigatório.", text_color="red")
        return is_valid

    def _validate_username_live(self, event=None):
        """Valida o formato do nome de utilizador em tempo real e exibe feedback com ícone."""
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
            self.username_validation_label.configure(text="✔️ Nome de utilizador válido", text_color="green")
        else:
            self.username_entry.configure(border_color="red")
            self.username_validation_label.configure(text=f"❌ Nome de utilizador inválido: {message}", text_color="red")

        return is_valid

    def _validate_company_live(self, event=None):
        """Valida o campo Departamento/Empresa em tempo real, se visível, e exibe feedback com ícone."""
        selected_role = self.role_combobox.get()
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(selected_role)

        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_combobox.get().strip()
            is_valid = bool(company_name)
            if is_valid:
                self.company_combobox.configure(border_color=self.default_border_color)
                self.company_validation_label.configure(text="✔️ Seleção válida", text_color="green")
            else:
                self.company_combobox.configure(border_color="red")
                self.company_validation_label.configure(text="❌ A seleção do departamento/empresa é obrigatória.", text_color="red")
            return is_valid
        elif main_group == "67_TELECOM":
            # Para 67_TELECOM, o subgrupo é obrigatório
            sub_group_selected = self.subgroup_67_combobox.get().strip()
            is_valid = bool(sub_group_selected)
            if is_valid:
                self.subgroup_67_combobox.configure(border_color=self.default_border_color)
                self.company_validation_label.configure(text="✔️ Subgrupo válido", text_color="green") # Reutiliza o label para feedback
            else:
                self.subgroup_67_combobox.configure(border_color="red")
                self.company_validation_label.configure(text="❌ A seleção do subgrupo é obrigatória.", text_color="red")
            return is_valid

        # Se o campo não é visível, não há validação para ele e feedback é limpo
        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")
        if hasattr(self, 'subgroup_67_combobox'): # Assegura que o widget existe antes de tentar configurar
            self.subgroup_67_combobox.configure(border_color=self.default_border_color)
        return True

    def _on_role_selected(self, selected_role):
        """Mostra ou esconde o campo de empresa/departamento com base no vínculo."""
        if selected_role == "Parceiro":
            self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
            self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))

            self.company_label.configure(text="Selecione a Empresa Parceira:")
            self.company_combobox.configure(values=[c for c in self.partner_list if c != "67 INTERNET"]) # Excluir 67 Internet daqui
            self.company_combobox.set(self.company_combobox._values[0] if self.company_combobox._values else "")

            # Esconder subgrupo 67
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        elif selected_role == "Prefeitura":
            self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
            self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))

            self.company_label.configure(text="Selecione o Departamento:")
            self.company_combobox.configure(values=self.prefeitura_dept_list)
            self.company_combobox.set(self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")

            # Esconder subgrupo 67
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        elif selected_role == "Colaboradores 67":
            # Esconder campos de empresa/departamento
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()

            # Mostrar campos de subgrupo para 67 Telecom
            self.subgroup_67_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.subgroup_67_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,10))
            # O novo padrão é "67_TELECOM_USER"
            self.subgroup_67_combobox.set("67_TELECOM_USER") # Definindo 67_TELECOM_USER como padrão

        else: # Outros casos, esconder tudo
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        self._validate_company_live()


    def on_show(self):
        """Limpa os campos do formulário e reseta feedback visual sempre que a tela é exibida."""
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()
        self.name_entry.focus_set() # Define o foco inicial

    def submit(self):
        """Coleta os dados do formulário e os envia para o controlador, com validação completa."""
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(self.role_combobox.get())

        company_name = None
        # sub_group agora será definido pelo combobox, não mais um padrão fixo "USER"
        sub_group = self.subgroup_67_combobox.get() if main_group == "67_TELECOM" else None # Alterado para None como fallback

        if main_group == "PARTNER":
            company_name = self.company_combobox.get()
        elif main_group == "PREFEITURA":
            company_name = self.company_combobox.get()
        elif main_group == "67_TELECOM":
            # sub_group já foi obtido acima
            if sub_group == "67_INTERNET_USER":
                company_name = "67 INTERNET" # Define a empresa automaticamente para este subgrupo
            elif sub_group == "67_TELECOM_USER": # Nova condição para 67_TELECOM_USER
                company_name = "67 TELECOM" # Define a empresa como "67 TELECOM"
            # Para outros sub_groups como ADMIN, MANAGER, SUPER_ADMIN, company_name permanece None ou vazio, o que é aceitável.
            # Se o sub_group for ADMIN, MANAGER, SUPER_ADMIN, a company_name pode ser vazia ou '67 TELECOM' conforme a necessidade de relatório.
            # Para manter a consistência, se não for 67_INTERNET_USER ou 67_TELECOM_USER, e o main_group for 67_TELECOM, defina como '67 TELECOM'.
            elif sub_group in ["ADMIN", "MANAGER", "SUPER_ADMIN"]:
                company_name = "67 TELECOM" # Define a empresa como 67 TELECOM para estes subgrupos

        # --- Validações Finais Antes da Submissão ---
        all_valid = True

        if not self._validate_name_live():
            all_valid = False

        if not self._validate_username_live():
            all_valid = False

        if main_group in ["PARTNER", "PREFEITURA"] and not self._validate_company_live():
            all_valid = False
        elif main_group == "67_TELECOM" and not self._validate_company_live(): # Valida o subgrupo para 67_TELECOM
            all_valid = False

        if not all_valid:
            messagebox.showwarning("Campos Inválidos", "Por favor, corrija os campos destacados em vermelho antes de enviar a solicitação.")
            return

        self.controller.submit_access_request(full_name, username, main_group, sub_group, company_name)


class PendingApprovalView(ctk.CTkFrame):
    """Tela mostrada enquanto o acesso do usuário está pendente de aprovação."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        title = ctk.CTkLabel(center_frame, text="Acesso Pendente",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        title.pack(pady=(0, 10))

        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação de um administrador. O status será verificado a cada 30 segundos.",
                                wraplength=450, text_color="gray70")
        subtitle.pack(pady=(0, 20))

        # Novo rótulo para feedback visual
        self.status_label = ctk.CTkLabel(center_frame, text="A verificar o status...",
                                         font=ctk.CTkFont(size=14, slant="italic"),
                                         text_color=self.controller.ACCENT_COLOR)
        self.status_label.pack(pady=(0, 10))

        # Botão para verificação manual
        check_button = ctk.CTkButton(center_frame, text="Verificar Agora", command=self.check_status_now,
                                      fg_color=self.controller.PRIMARY_COLOR, hover_color=self.controller.ACCENT_COLOR)
        check_button.pack(pady=(0, 10))

        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                      fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        logout_button.pack()

        self.is_running = False
        self.checker_thread = None

    def on_show(self):
        """Método chamado quando a tela é exibida."""
        # Se o thread não estiver a correr ou não estiver vivo, inicia-o.
        if not self.is_running or (self.checker_thread and not self.checker_thread.is_alive()):
            self.is_running = True
            self.checker_thread = threading.Thread(target=self._check_status_thread, daemon=True)
            self.checker_thread.start()

    def _check_status_thread(self):
        """Thread que verifica o status do usuário a cada 30 segundos."""
        while self.is_running:
            # Atualiza o rótulo de status na thread principal
            self.controller.after(0, lambda: self.status_label.configure(text="A verificar o status..."))

            # Força o refresh do perfil do usuário na planilha
            user_profile = self.controller.sheets_service.check_user_status(self.controller.user_email)
            status = user_profile.get("status")

            if status == "approved":
                self.is_running = False # Para o loop do thread
                self.controller.user_profile = user_profile # Atualiza o perfil no controlador
                # Navega para o próximo ecrã na thread principal
                self.controller.after(0, self.controller.navigate_based_on_status)
            elif status == "rejected":
                self.is_running = False # Para o loop do thread
                self.controller.after(0, lambda: messagebox.showerror("Acesso Negado", "Sua solicitação de acesso foi rejeitada. Por favor, entre em contacto com o administrador."))
                # Realiza logout na thread principal
                self.controller.after(0, self.controller.perform_logout)
            else:
                # Se ainda pendente, atualiza a mensagem e aguarda
                self.controller.after(0, lambda: self.status_label.configure(text=f"Aguardando aprovação. Próxima verificação em 30 segundos..."))

            # Pausa o thread, mas verifica se self.is_running ainda é True antes de dormir
            # para permitir paragem rápida se o status mudar.
            for _ in range(30): # Dorme por 30 segundos, verificando a cada segundo
                if not self.is_running:
                    break
                time.sleep(1)

    def check_status_now(self):
        """Verifica o status imediatamente ao clicar no botão."""
        if self.is_running:
            # Para o thread atual para que uma nova verificação comece imediatamente
            self.is_running = False
            # Pequena pausa para garantir que o thread atual possa terminar o seu sleep se estiver a correr
            if self.checker_thread and self.checker_thread.is_alive():
                self.checker_thread.join(timeout=1)

            # Reinicia o processo de verificação
            self.is_running = True
            self.status_label.configure(text="A verificar o status agora...")
            self.checker_thread = threading.Thread(target=self._check_status_thread, daemon=True)
            self.checker_thread.start()
