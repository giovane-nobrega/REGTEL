# ==============================================================================
# FICHEIRO: src/views/main_menu_view.py
# DESCRIÇÃO: Contém a classe de interface para o menu principal da aplicação REGTEL.
#            Exibe botões de ação dinamicamente com base no perfil do utilizador logado.
# ==============================================================================

import customtkinter as ctk # Biblioteca CustomTkinter para interface gráfica
from builtins import super # CORRIGIDO: Importa 'super' explicitamente para satisfazer o Pylance

class MainMenuView(ctk.CTkFrame):
    """
    Menu principal da aplicação, com botões dinâmicos baseados no perfil do
    utilizador logado. Controla quais funcionalidades o utilizador pode aceder.
    """
    def __init__(self, parent, controller):
        """
        Inicializa a MainMenuView.
        :param parent: O widget pai (geralmente a instância da classe App).
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller # Armazena a referência ao controlador principal

        self.configure(fg_color=self.controller.BASE_COLOR) # Define a cor de fundo da tela

        # --- Configuração de Responsividade com Grid ---
        # A coluna 0 se expande para centralizar o conteúdo.
        self.grid_columnconfigure(0, weight=1)
        # As linhas 0 e 10 atuam como "espaçadores" que se expandem,
        # empurrando o conteúdo principal para o centro verticalmente.
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(10, weight=1)

        # Rótulo de título/boas-vindas do menu principal.
        self.title_label = ctk.CTkLabel(self, text="Menu Principal",
                                        font=ctk.CTkFont(size=28, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.grid(row=1, column=0, pady=(0, 40)) # Posiciona o título

        # --- Definição de todos os botões possíveis com cores e ícones Unicode ---
        # Ícones unicode sólidos e preenchidos para uma melhor aparência.
        ICON_DASHBOARD = "📊" # Ícone para dashboard
        ICON_CALL_DETAILED = "📞" # Ícone para chamada detalhada
        ICON_CALL_SIMPLE = "☎️" # Ícone para chamada simplificada
        ICON_EQUIPMENT = "⚙️" # Ícone para equipamento
        ICON_HISTORY = "📚" # Ícone para histórico
        ICON_LOGOUT = "➡️" # Ícone para logout (seta para fora)
        ICON_EXIT = "❌" # Ícone para fechar aplicação

        # Botão para aceder ao Dashboard de Gestão (apenas para administradores).
        self.admin_button = ctk.CTkButton(self, text=f"{ICON_DASHBOARD} Dashboard de Gestão",
                                          command=lambda: self.controller.show_frame("AdminDashboardView"),
                                          height=45, width=350, font=ctk.CTkFont(size=14, weight="bold"),
                                          fg_color=self.controller.PRIMARY_COLOR,
                                          text_color=self.controller.TEXT_COLOR,
                                          hover_color=self.controller.ACCENT_COLOR,
                                          compound="left") # Alinha o ícone à esquerda do texto

        # Botão para registar Ocorrência de Chamada (Detalhado) (para Parceiros e 67 Telecom).
        self.partner_button = ctk.CTkButton(self, text=f"{ICON_CALL_DETAILED} Registrar Ocorrência de Chamada (Detalhado)",
                                            command=lambda: self.controller.show_frame("RegistrationView"),
                                            height=45, width=350, font=ctk.CTkFont(size=14),
                                            fg_color=self.controller.PRIMARY_COLOR,
                                            text_color=self.controller.TEXT_COLOR,
                                            hover_color=self.controller.ACCENT_COLOR,
                                            compound="left")

        # Botão para registar Ocorrência de Chamada (Simplificado) (para Prefeitura).
        self.prefeitura_call_button = ctk.CTkButton(self, text=f"{ICON_CALL_SIMPLE} Registrar Ocorrência de Chamada (Simplificado)",
                                                    command=lambda: self.controller.show_frame("SimpleCallView"),
                                                    height=45, width=350, font=ctk.CTkFont(size=14),
                                                    fg_color=self.controller.PRIMARY_COLOR,
                                                    text_color=self.controller.TEXT_COLOR,
                                                    hover_color=self.controller.ACCENT_COLOR,
                                                    compound="left")

        # Botão para registar Suporte Técnico de Equipamento (para Prefeitura).
        self.prefeitura_equip_button = ctk.CTkButton(self, text=f"{ICON_EQUIPMENT} Registrar Suporte Técnico de Equipamento",
                                                     command=lambda: self.controller.show_frame("EquipmentView"),
                                                     height=45, width=350, font=ctk.CTkFont(size=14),
                                                     fg_color=self.controller.PRIMARY_COLOR,
                                                     text_color=self.controller.TEXT_COLOR,
                                                     hover_color=self.controller.ACCENT_COLOR,
                                                     compound="left")

        # Botão para ver o Histórico de Ocorrências (comum a todos os perfis).
        self.history_button = ctk.CTkButton(self, text=f"{ICON_HISTORY} Ver Histórico de Ocorrências",
                                            command=lambda: self.controller.show_frame("HistoryView"),
                                            height=45, width=350, font=ctk.CTkFont(size=14),
                                            fg_color=self.controller.PRIMARY_COLOR,
                                            text_color=self.controller.TEXT_COLOR,
                                            hover_color=self.controller.ACCENT_COLOR,
                                            compound="left")

        # Botão para Logout (comum a todos os perfis).
        self.logout_button = ctk.CTkButton(self, text=f"{ICON_LOGOUT} Logout (Trocar de usuário)",
                                           command=self.controller.perform_logout,
                                           height=45, width=350, font=ctk.CTkFont(size=14),
                                           fg_color=self.controller.DANGER_COLOR,
                                           text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.DANGER_HOVER_COLOR,
                                           compound="left")

        # Botão para Fechar a Aplicação (comum a todos os perfis).
        self.exit_button = ctk.CTkButton(self, text=f"{ICON_EXIT} Fechar Aplicação",
                                         command=self.controller.quit,
                                         height=45, width=350, font=ctk.CTkFont(size=14),
                                         fg_color=self.controller.GRAY_BUTTON_COLOR,
                                         text_color=self.controller.TEXT_COLOR,
                                         hover_color=self.controller.GRAY_HOVER_COLOR,
                                         compound="left")

        # Rótulo para exibir o e-mail do utilizador logado.
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                         text_color="gray70")
        self.status_label.grid(row=11, column=0, padx=20, pady=10, sticky="ew")

        # NOVO: Rótulo para exibir a versão da aplicação.
        self.version_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10),
                                          text_color="gray50")
        # Posicionado na última linha, com padding para não ficar colado na borda.
        self.version_label.grid(row=12, column=0, padx=20, pady=(0, 5), sticky="ew")


    def update_user_info(self, email, user_profile, app_version):
        """
        Atualiza a mensagem de boas-vindas, o e-mail do utilizador logado e a versão da aplicação.
        Chama a função para exibir/esconder os botões de menu com base no perfil.
        :param email: E-mail do utilizador logado.
        :param user_profile: Dicionário com os dados do perfil do utilizador.
        :param app_version: A string da versão atual da aplicação.
        """
        username = user_profile.get("username", "")
        welcome_name = user_profile.get("name", username) # Usa o nome completo se disponível
        self.title_label.configure(text=f"Bem-vindo, {welcome_name}!") # Atualiza o título de boas-vindas
        self.status_label.configure(text=f"Login como: {email}") # Exibe o e-mail logado
        self.version_label.configure(text=f"Versão: {app_version}") # Exibe a versão da aplicação
        self.update_buttons(user_profile) # Atualiza a visibilidade dos botões

    def update_buttons(self, user_profile):
        """
        Mostra ou esconde os botões de menu com base no perfil do utilizador logado.
        Garante que apenas as opções relevantes para o perfil sejam visíveis.
        :param user_profile: Dicionário com os dados do perfil do utilizador.
        """
        # Esconde todos os botões de perfil inicialmente.
        for widget in (self.admin_button, self.partner_button, self.prefeitura_call_button, self.prefeitura_equip_button):
            widget.grid_forget() # Remove o widget do layout

        main_group = user_profile.get("main_group")
        sub_group = user_profile.get("sub_group")

        next_row = 2 # Define a linha inicial para posicionar os botões de perfil

        # Lógica para exibir botões com base no grupo principal e subgrupo.
        if main_group == "67_TELECOM" and sub_group == "SUPER_ADMIN":
            # SUPER_ADMIN tem acesso a todas as funcionalidades de gestão e registo.
            self.title_label.configure(text=f"Menu Super Admin: {user_profile.get('name')}")
            self.admin_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
            self.partner_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
            self.prefeitura_call_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
            self.prefeitura_equip_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1

        elif main_group == "67_TELECOM":
            # ADMIN tem acesso ao dashboard de gestão e registo detalhado.
            if sub_group == "ADMIN":
                self.admin_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
                self.partner_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
            # MANAGER, 67_TELECOM_USER e 67_INTERNET_USER têm acesso apenas ao registo detalhado.
            elif sub_group in ["MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"]:
                self.partner_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1

        elif main_group == "PARTNER":
            # Parceiros têm acesso ao registo detalhado.
            self.partner_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1

        elif main_group == "PREFEITURA":
            # Prefeitura tem acesso ao registo simplificado e de equipamento.
            self.prefeitura_call_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1
            self.prefeitura_equip_button.grid(row=next_row, column=0, pady=8, padx=20); next_row += 1

        # Botões comuns a todos os perfis (Histórico, Logout, Fechar Aplicação).
        self.history_button.grid(row=next_row, column=0, pady=8, padx=20)
        next_row += 1

        # Adiciona um espaçamento maior antes dos botões de saída para melhor separação visual.
        self.logout_button.grid(row=next_row, column=0, pady=(20, 8), padx=20)
        next_row += 1

        self.exit_button.grid(row=next_row, column=0, pady=8, padx=20)

