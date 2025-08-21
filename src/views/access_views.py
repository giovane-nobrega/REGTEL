# ==============================================================================
# FICHEIRO: src/views/access_views.py
# DESCRIÇÃO: Contém as classes de interface para o fluxo de solicitação
#            e aprovação de acesso de novos utilizadores.
#            Inclui validações, agrupamento de campos e feedback visual.
# ==============================================================================

import customtkinter as ctk  # Biblioteca CustomTkinter para interface gráfica
# Usado para exibir caixas de mensagem de alerta/erro
from tkinter import messagebox
import re  # Módulo para expressões regulares (usado em validações)
import threading  # Usado para executar verificações de status em segundo plano
import time  # Usado para pausas em threads (na verificação de status)


class RequestAccessView(ctk.CTkFrame):
    """
    Tela para novos utilizadores solicitarem acesso ao sistema REGTEL.
    Permite que o utilizador preencha seus dados pessoais e de vínculo.
    """

    def __init__(self, parent, controller):
        """
        Inicializa a RequestAccessView.
        :param parent: O widget pai (geralmente a instância da classe App).
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller  # Armazena a referência ao controlador principal

        # Define a cor de fundo da tela
        self.configure(fg_color=self.controller.BASE_COLOR)

        # Listas de opções para ComboBoxes de empresas/departamentos.
        # "67 INTERNET" é excluído de partner_list pois é um subgrupo de 67_TELECOM.
        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA",
                             "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS",
                                     "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        # Configuração de responsividade da grade (grid) da tela.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Frame central para agrupar os widgets e centralizá-los.
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        # Rótulos de título e subtítulo da tela.
        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.",
                                wraplength=400, text_color="gray70")

        title.pack(pady=(0, 10))
        subtitle.pack(pady=(0, 20))

        # --- FRAME PARA DADOS PESSOAIS ---
        # Agrupa os campos de nome completo e nome de utilizador.
        personal_data_frame = ctk.CTkFrame(
            center_frame, fg_color="gray15", corner_radius=10)
        personal_data_frame.pack(
            pady=(10, 10), padx=20, fill="x", expand=False)
        personal_data_frame.grid_columnconfigure(
            0, weight=1)  # Coluna para rótulos
        personal_data_frame.grid_columnconfigure(
            1, weight=3)  # Coluna para campos de entrada

        ctk.CTkLabel(personal_data_frame, text="Dados Pessoais", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # Campo Nome Completo
        self.name_label = ctk.CTkLabel(
            personal_data_frame, text="Nome Completo:", text_color=self.controller.TEXT_COLOR)
        self.name_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 0))
        self.name_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Digite seu nome completo", width=300,
                                       fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                       border_color="gray40")
        self.name_entry.grid(row=1, column=1, sticky="ew",
                             padx=15, pady=(5, 0))
        # Rótulo para feedback de validação do nome.
        self.name_validation_label = ctk.CTkLabel(
            personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.name_validation_label.grid(
            row=2, column=1, sticky="w", padx=15, pady=(0, 10))

        # Campo Nome de Utilizador
        self.username_label = ctk.CTkLabel(
            personal_data_frame, text="Nome de Usuário:", text_color=self.controller.TEXT_COLOR)
        self.username_label.grid(
            row=3, column=0, sticky="w", padx=15, pady=(5, 0))
        self.username_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Ex: jsilva (4-16 caracteres, sem espaços)", width=300,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.username_entry.grid(
            row=3, column=1, sticky="ew", padx=15, pady=(5, 0))
        # Rótulo para feedback de validação do nome de utilizador.
        self.username_validation_label = ctk.CTkLabel(
            personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.username_validation_label.grid(
            row=4, column=1, sticky="w", padx=15, pady=(0, 10))

        # --- FRAME PARA DADOS DE VÍNCULO ---
        # Agrupa os campos de vínculo principal, departamento/empresa e subgrupo.
        affiliation_data_frame = ctk.CTkFrame(
            center_frame, fg_color="gray15", corner_radius=10)
        affiliation_data_frame.pack(
            pady=(10, 10), padx=20, fill="x", expand=False)
        affiliation_data_frame.grid_columnconfigure(
            0, weight=1)  # Coluna para rótulos
        affiliation_data_frame.grid_columnconfigure(
            1, weight=3)  # Coluna para campos de entrada

        ctk.CTkLabel(affiliation_data_frame, text="Dados de Vínculo", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # ComboBox para Vínculo Principal (Role)
        self.role_label = ctk.CTkLabel(
            affiliation_data_frame, text="Vínculo Principal:", text_color=self.controller.TEXT_COLOR)
        self.role_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 0))
        self.role_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected,
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        self.role_combobox.grid(
            row=1, column=1, sticky="ew", padx=15, pady=(5, 10))

        # ComboBox para Departamento/Empresa (Condicional, visibilidade controlada por _on_role_selected)
        self.company_label = ctk.CTkLabel(
            affiliation_data_frame, text="Departamento/Empresa:", text_color=self.controller.TEXT_COLOR)
        self.company_label.grid(
            row=2, column=0, sticky="w", padx=15, pady=(5, 0))
        self.company_combobox = ctk.CTkComboBox(affiliation_data_frame, values=[], width=300,
                                                fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                button_hover_color=self.controller.ACCENT_COLOR)
        self.company_combobox.grid(
            row=2, column=1, sticky="ew", padx=15, pady=(5, 0))
        # Rótulo para feedback de validação da empresa/departamento.
        self.company_validation_label = ctk.CTkLabel(
            affiliation_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.company_validation_label.grid(
            row=3, column=1, sticky="w", padx=15, pady=(0, 10))

        # ComboBox para Subgrupo dentro de "Colaboradores 67" (Condicional)
        self.subgroup_67_label = ctk.CTkLabel(
            affiliation_data_frame, text="Selecione o Subgrupo:", text_color=self.controller.TEXT_COLOR)
        # REMOVIDO: "MANAGER", "ADMIN", "SUPER_ADMIN" da lista de valores para auto-registo
        self.subgroup_67_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["67_TELECOM_USER", "67_INTERNET_USER"],
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                    button_hover_color=self.controller.ACCENT_COLOR)

        # --- Botões de Ação ---
        # Botão para enviar a solicitação de acesso.
        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40,
                                           fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        self.submit_button.pack(pady=20, padx=20, fill="x")

        # Botão para sair da aplicação (logout).
        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                           fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        self.logout_button.pack(pady=10, padx=20, fill="x")

        # --- Configuração da Lógica de Validação Proativa e Foco ---
        # Armazena a cor da borda padrão para resetar validações
        self.default_border_color = self.name_entry.cget("border_color")

        # Vincula eventos de teclado e foco a funções de validação e feedback visual.
        self.name_entry.bind("<KeyRelease>", self._validate_name_live)
        self.name_entry.bind("<FocusOut>", self._validate_name_live)
        self.name_entry.bind(
            "<FocusIn>", lambda e: self._on_focus_in(self.name_label))
        self.name_entry.bind(
            "<FocusOut>", lambda e: self._on_focus_out(self.name_label))

        self.username_entry.bind("<KeyRelease>", self._validate_username_live)
        self.username_entry.bind("<FocusOut>", self._validate_username_live)
        self.username_entry.bind(
            "<FocusIn>", lambda e: self._on_focus_in(self.username_label))
        self.username_entry.bind(
            "<FocusOut>", lambda e: self._on_focus_out(self.username_label))

        self.company_combobox.bind(
            "<<ComboboxSelected>>", self._validate_company_live)
        self.role_combobox.bind("<<ComboboxSelected>>",
                                self._validate_company_live)
        self.company_combobox.bind(
            "<FocusIn>", lambda e: self._on_focus_in(self.company_label))
        self.company_combobox.bind(
            "<FocusOut>", lambda e: self._on_focus_out(self.company_label))
        self.role_combobox.bind(
            "<FocusIn>", lambda e: self._on_focus_in(self.role_label))
        self.role_combobox.bind(
            "<FocusOut>", lambda e: self._on_focus_out(self.role_label))

        self.subgroup_67_combobox.bind(
            "<<ComboboxSelected>>", self._validate_company_live)  # Revalida ao mudar subgrupo
        self.subgroup_67_combobox.bind(
            "<FocusIn>", lambda e: self._on_focus_in(self.subgroup_67_label))
        self.subgroup_67_combobox.bind(
            "<FocusOut>", lambda e: self._on_focus_out(self.subgroup_67_label))

        # Define o estado inicial da UI ao carregar a tela.
        # Define o valor inicial padrão para o vínculo principal
        self.role_combobox.set("Prefeitura")
        # Chama a função para configurar os campos dependentes
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()  # Limpa qualquer feedback de validação anterior

    def _on_focus_in(self, label_widget):
        """
        Aplica um estilo visual (negrito e tamanho maior) ao rótulo de um campo
        quando o campo de entrada associado recebe foco.
        :param label_widget: O widget CTkLabel a ser estilizado.
        """
        label_widget.configure(font=ctk.CTkFont(weight="bold", size=14))

    def _on_focus_out(self, label_widget):
        """
        Remove o estilo visual de foco do rótulo de um campo
        quando o campo de entrada associado perde o foco.
        :param label_widget: O widget CTkLabel a ser estilizado.
        """
        label_widget.configure(font=ctk.CTkFont(weight="normal", size=13))

    def _reset_validation_feedback(self):
        """
        Reseta as cores das bordas dos campos de entrada e limpa as mensagens de erro/validação.
        """
        self.name_entry.configure(border_color=self.default_border_color)
        self.name_validation_label.configure(text="")

        self.username_entry.configure(border_color=self.default_border_color)
        self.username_validation_label.configure(text="")

        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")

        # Garante que o combobox de subgrupo também seja resetado se estiver visível.
        if hasattr(self, 'subgroup_67_combobox'):
            self.subgroup_67_combobox.configure(
                border_color=self.default_border_color)

    def _validate_name_live(self, event=None):
        """
        Valida o campo 'Nome Completo' em tempo real (ao digitar ou perder o foco).
        Exibe feedback visual (borda vermelha/padrão, mensagem de validação).
        :param event: O evento que acionou a validação (opcional).
        :return: True se o nome for válido, False caso contrário.
        """
        name = self.name_entry.get().strip()  # Obtém o texto e remove espaços em branco
        is_valid = bool(name)  # Considera válido se não estiver vazio
        if is_valid:
            self.name_entry.configure(border_color=self.default_border_color)
            self.name_validation_label.configure(
                text="✔️ Nome válido", text_color="green")
        else:
            self.name_entry.configure(border_color="red")
            self.name_validation_label.configure(
                text="❌ O nome completo é obrigatório.", text_color="red")
        return is_valid

    def _validate_username_live(self, event=None):
        """
        Valida o formato do 'Nome de Usuário' em tempo real.
        Verifica comprimento (4-16 caracteres) e caracteres permitidos (letras, números, _, .).
        Exibe feedback visual.
        :param event: O evento que acionou a validação (opcional).
        :return: True se o nome de utilizador for válido, False caso contrário.
        """
        username = self.username_entry.get()
        is_valid = True
        message = ""

        if not username.strip():
            is_valid = False
            message = "O nome de utilizador é obrigatório."
        elif not (4 <= len(username) <= 16):
            is_valid = False
            message = "Deve ter entre 4 e 16 caracteres."
        # Permite letras, números, _ e .
        elif not re.fullmatch(r"^[a-zA-Z0-9_.]*$", username):
            is_valid = False
            message = "Não pode conter espaços ou caracteres especiais (exceto _ e .)."

        if is_valid:
            self.username_entry.configure(
                border_color=self.default_border_color)
            self.username_validation_label.configure(
                text="✔️ Nome de utilizador válido", text_color="green")
        else:
            self.username_entry.configure(border_color="red")
            self.username_validation_label.configure(
                text=f"❌ Nome de utilizador inválido: {message}", text_color="red")

        return is_valid

    def _validate_company_live(self, event=None):
        """
        Valida o campo 'Departamento/Empresa' ou 'Subgrupo' em tempo real,
        dependendo do vínculo principal selecionado.
        Exibe feedback visual.
        :param event: O evento que acionou a validação (opcional).
        :return: True se a seleção for válida, False caso contrário.
        """
        selected_role = self.role_combobox.get()
        role_map = {"Prefeitura": "PREFEITURA",
                    "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(selected_role)

        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_combobox.get().strip()
            is_valid = bool(company_name)  # Válido se não estiver vazio
            if is_valid:
                self.company_combobox.configure(
                    border_color=self.default_border_color)
                self.company_validation_label.configure(
                    text="✔️ Seleção válida", text_color="green")
            else:
                self.company_combobox.configure(border_color="red")
                self.company_validation_label.configure(
                    text="❌ A seleção do departamento/empresa é obrigatória.", text_color="red")
            return is_valid
        elif main_group == "67_TELECOM":
            # Para 'Colaboradores 67', o subgrupo é obrigatório.
            sub_group_selected = self.subgroup_67_combobox.get().strip()
            is_valid = bool(sub_group_selected)  # Válido se não estiver vazio
            if is_valid:
                self.subgroup_67_combobox.configure(
                    border_color=self.default_border_color)
                self.company_validation_label.configure(
                    text="✔️ Subgrupo válido", text_color="green")  # Reutiliza o label para feedback
            else:
                self.subgroup_67_combobox.configure(border_color="red")
                self.company_validation_label.configure(
                    text="❌ A seleção do subgrupo é obrigatória.", text_color="red")
            return is_valid

        # Se o campo não é visível (ex: nenhum vínculo selecionado que exija),
        # não há validação para ele e o feedback é limpo.
        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")
        if hasattr(self, 'subgroup_67_combobox'):
            self.subgroup_67_combobox.configure(
                border_color=self.default_border_color)
        return True

    def _on_role_selected(self, selected_role):
        """
        Função chamada quando o utilizador seleciona um vínculo principal (role).
        Controla a visibilidade e as opções dos ComboBoxes de departamento/empresa e subgrupo.
        :param selected_role: O valor selecionado no ComboBox de vínculo principal.
        """
        if selected_role == "Parceiro":
            # Mostra o campo de empresa e configura suas opções para parceiros.
            self.company_label.grid(
                row=2, column=0, sticky="w", padx=15, pady=(5, 0))
            self.company_combobox.grid(
                row=2, column=1, sticky="ew", padx=15, pady=(5, 0))
            self.company_validation_label.grid(
                row=3, column=1, sticky="w", padx=15, pady=(0, 10))

            self.company_label.configure(text="Selecione a Empresa Parceira:")
            # Exclui "67 INTERNET" da lista de parceiros, pois é um subgrupo específico.
            self.company_combobox.configure(
                values=[c for c in self.partner_list if c != "67 INTERNET"])
            self.company_combobox.set(
                self.company_combobox._values[0] if self.company_combobox._values else "")

            # Esconde o ComboBox de subgrupo 67.
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        elif selected_role == "Prefeitura":
            # Mostra o campo de departamento e configura suas opções para prefeitura.
            self.company_label.grid(
                row=2, column=0, sticky="w", padx=15, pady=(5, 0))
            self.company_combobox.grid(
                row=2, column=1, sticky="ew", padx=15, pady=(5, 0))
            self.company_validation_label.grid(
                row=3, column=1, sticky="w", padx=15, pady=(0, 10))

            self.company_label.configure(text="Selecione o Departamento:")
            self.company_combobox.configure(values=self.prefeitura_dept_list)
            self.company_combobox.set(
                self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")

            # Esconde o ComboBox de subgrupo 67.
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        elif selected_role == "Colaboradores 67":
            # Esconde os campos de empresa/departamento.
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()

            # Mostra os campos de subgrupo para 67 Telecom.
            self.subgroup_67_label.grid(
                row=2, column=0, sticky="w", padx=15, pady=(5, 0))
            self.subgroup_67_combobox.grid(
                row=2, column=1, sticky="ew", padx=15, pady=(5, 10))
            # Define "67_TELECOM_USER" como a opção padrão para colaboradores 67 Telecom.
            self.subgroup_67_combobox.set("67_TELECOM_USER")

        else:  # Para qualquer outro caso ou estado inicial, esconde todos os campos dependentes.
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()

        # Revalida os campos após a mudança de vínculo.
        self._validate_company_live()

    def on_show(self):
        """
        Método chamado sempre que a tela 'RequestAccessView' é exibida.
        Limpa os campos do formulário, reseta o feedback visual e define o foco inicial.
        """
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        # Define o valor padrão para o vínculo
        self.role_combobox.set("Prefeitura")
        # Aciona a lógica de visibilidade de campos dependentes
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()  # Limpa as bordas vermelhas e mensagens de erro
        self.name_entry.focus_set()  # Define o foco inicial no campo de nome completo

    def submit(self):
        """
        Coleta os dados do formulário de solicitação de acesso, realiza validações finais
        e os envia para o controlador para processamento.
        """
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        role_map = {"Prefeitura": "PREFEITURA",
                    "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(self.role_combobox.get())

        company_name = None
        sub_group = None  # Inicializa sub_group

        # Lógica para definir o sub_group e company_name com base no main_group e regras do documento
        if main_group == "PARTNER":
            sub_group = "USER"  # Parceiros devem ter subgrupo "USER"
            # Empresa é a selecionada no combobox
            company_name = self.company_combobox.get()
        elif main_group == "PREFEITURA":
            sub_group = "PREFEITURA_USER"  # Prefeitura deve ter subgrupo "PREFEITURA_USER"
            # Empresa/Departamento é a selecionada no combobox
            company_name = self.company_combobox.get()
        elif main_group == "67_TELECOM":
            # Subgrupo é o selecionado no combobox
            sub_group = self.subgroup_67_combobox.get()
            # Para 67_TELECOM, a empresa é SEMPRE TRR, independentemente do subgrupo.
            company_name = "TRR"

        # --- Validações Finais Antes da Submissão ---
        all_valid = True

        # Valida todos os campos obrigatórios.
        if not self._validate_name_live():
            all_valid = False
        if not self._validate_username_live():
            all_valid = False
        # Valida o campo de empresa/departamento ou subgrupo, dependendo do vínculo.
        if main_group in ["PARTNER", "PREFEITURA"] and not self._validate_company_live():
            all_valid = False
        elif main_group == "67_TELECOM" and not self._validate_company_live():
            all_valid = False

        if not all_valid:
            messagebox.showwarning(
                "Campos Inválidos", "Por favor, corrija os campos destacados em vermelho antes de enviar a solicitação.")
            return

        # Envia a solicitação de acesso para o controlador.
        self.controller.submit_access_request(
            full_name, username, main_group, sub_group, company_name)


class PendingApprovalView(ctk.CTkFrame):
    """
    Tela exibida enquanto o acesso do utilizador está pendente de aprovação por um administrador.
    Verifica o status do acesso periodicamente em segundo plano.
    """

    def __init__(self, parent, controller):
        """
        Inicializa a PendingApprovalView.
        :param parent: O widget pai.
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        # Rótulos de título e subtítulo da tela.
        title = ctk.CTkLabel(center_frame, text="Acesso Pendente",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        title.pack(pady=(0, 10))

        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação de um administrador. O status será verificado a cada 30 segundos.",
                                wraplength=450, text_color="gray70")
        subtitle.pack(pady=(0, 20))

        # Rótulo para feedback visual do status da verificação.
        self.status_label = ctk.CTkLabel(center_frame, text="A verificar o status...",
                                         font=ctk.CTkFont(
                                             size=14, slant="italic"),
                                         text_color=self.controller.ACCENT_COLOR)
        self.status_label.pack(pady=(0, 10))

        # Botão para forçar uma verificação manual do status.
        check_button = ctk.CTkButton(center_frame, text="Verificar Agora", command=self.check_status_now,
                                     fg_color=self.controller.PRIMARY_COLOR, hover_color=self.controller.ACCENT_COLOR)
        check_button.pack(pady=(0, 10))

        # Botão para sair da aplicação (logout).
        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                      fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        logout_button.pack()

        self.is_running = False  # Flag para controlar o loop da thread de verificação
        self.checker_thread = None  # Referência à thread de verificação

    def on_show(self):
        """
        Método chamado quando a tela 'PendingApprovalView' é exibida.
        Inicia a thread de verificação de status se ela ainda não estiver a correr.
        """
        if not self.is_running or (self.checker_thread and not self.checker_thread.is_alive()):
            self.is_running = True
            # Thread daemon para fechar com a aplicação
            self.checker_thread = threading.Thread(
                target=self._check_status_thread, daemon=True)
            self.checker_thread.start()

    def _check_status_thread(self):
        """
        Thread que verifica o status do utilizador (aprovado/rejeitado) a cada 30 segundos.
        Atualiza a UI e navega se o status mudar.
        """
        while self.is_running:  # Loop continua enquanto a flag 'is_running' for True
            # Atualiza o rótulo de status na thread principal da UI.
            self.controller.after(0, lambda: self.status_label.configure(
                text="A verificar o status..."))

            # Força o refresh do perfil do utilizador na planilha (para obter o status mais recente).
            user_profile = self.controller.sheets_service.check_user_status(
                self.controller.user_email)
            status = user_profile.get("status")

            if status == "approved":
                self.is_running = False  # Para o loop do thread
                # Atualiza o perfil no controlador principal
                self.controller.user_profile = user_profile
                # Navega para o próximo ecrã
                self.controller.after(
                    0, self.controller.navigate_based_on_status)
            elif status == "rejected":
                self.is_running = False  # Para o loop do thread
                self.controller.after(0, lambda: messagebox.showerror(
                    "Acesso Negado", "Sua solicitação de acesso foi rejeitada. Por favor, entre em contacto com o administrador."))
                self.controller.after(
                    0, self.controller.perform_logout)  # Realiza logout
            else:
                # Se ainda pendente, atualiza a mensagem e aguarda.
                self.controller.after(0, lambda: self.status_label.configure(
                    text=f"Aguardando aprovação. Próxima verificação em 30 segundos..."))

            # Pausa o thread por 30 segundos, verificando a flag 'is_running' a cada segundo.
            # Isso permite que o thread pare rapidamente se o status mudar ou a aplicação fechar.
            for _ in range(30):
                if not self.is_running:
                    break
                time.sleep(1)

    def check_status_now(self):
        """
        Verifica o status imediatamente ao clicar no botão 'Verificar Agora'.
        Interrompe a thread atual e inicia uma nova verificação.
        """
        if self.is_running:
            self.is_running = False  # Sinaliza para a thread atual parar
            # Pequena pausa para garantir que a thread atual possa terminar o seu sleep.
            if self.checker_thread and self.checker_thread.is_alive():
                # Espera no máximo 1 segundo pela thread
                self.checker_thread.join(timeout=1)

            # Reinicia o processo de verificação em uma nova thread.
            self.is_running = True
            self.status_label.configure(text="A verificar o status agora...")
            self.checker_thread = threading.Thread(
                target=self._check_status_thread, daemon=True)
            self.checker_thread.start()
