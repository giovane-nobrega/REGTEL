# ==============================================================================
# FICHEIRO: src/views/main_menu_view.py
# DESCRIÇÃO: Contém a classe de interface para o menu principal da aplicação,
#            que exibe botões de ação dinamicamente com base no perfil do
#            utilizador. (VERSÃO CORRIGIDA)
# ==============================================================================

import customtkinter as ctk

class MainMenuView(ctk.CTkFrame):
    """
    Menu principal da aplicação, com botões dinâmicos baseados no perfil do
    utilizador logado.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Configuração da Responsividade com Grid ---
        self.grid_columnconfigure(0, weight=1)
        # Linhas espaçadoras (0 e 10) empurram o conteúdo para o centro
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(10, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Menu Principal", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=1, column=0, pady=(0, 40))
        
        # --- Definição de todos os botões possíveis ---
        self.admin_button = ctk.CTkButton(self, text="Dashboard de Gestão", command=lambda: self.controller.show_frame("AdminDashboardView"), height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#1F6AA5")
        self.partner_button = ctk.CTkButton(self, text="Registrar Ocorrência de Chamada (Detalhado)", command=lambda: self.controller.show_frame("RegistrationView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_call_button = ctk.CTkButton(self, text="Registrar Ocorrência de Chamada (Simplificado)", command=lambda: self.controller.show_frame("SimpleCallView"), height=45, width=350, font=ctk.CTkFont(size=14))
        self.prefeitura_equip_button = ctk.CTkButton(self, text="Registrar Suporte Técnico de Equipamento", command=lambda: self.controller.show_frame("EquipmentView"), height=45, width=350, font=ctk.CTkFont(size=14))
        
        self.history_button = ctk.CTkButton(self, text="Ver Histórico de Ocorrências", command=lambda: self.controller.show_frame("HistoryView"), height=45, width=350, font=ctk.CTkFont(size=14))
        
        self.logout_button = ctk.CTkButton(self, text="Logout (Trocar de usuário)", command=self.controller.perform_logout, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="#D32F2F", hover_color="#B71C1C")

        self.exit_button = ctk.CTkButton(self, text="Fechar Aplicação", command=self.controller.quit, height=45, width=350, font=ctk.CTkFont(size=14), fg_color="gray50", hover_color="gray40")
        
        # Label para mostrar o e-mail do utilizador logado
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=11, column=0, padx=20, pady=10, sticky="ew")

    def update_user_info(self, email, user_profile):
        """Atualiza a mensagem de boas-vindas e chama a atualização dos botões."""
        username = user_profile.get("username", "")
        welcome_name = user_profile.get("name", username) # Usa o nome completo se existir
        self.title_label.configure(text=f"Bem-vindo, {welcome_name}!")
        self.status_label.configure(text=f"Login como: {email}")
        # Chama a função que mostra os botões corretos
        self.update_buttons(user_profile)

    def update_buttons(self, user_profile):
        """Mostra ou esconde os botões com base no perfil do utilizador."""
        # Esconde todos os botões de perfil antes de mostrar os corretos
        for widget in (self.admin_button, self.partner_button, self.prefeitura_call_button, self.prefeitura_equip_button):
            widget.grid_forget()
        
        main_group = user_profile.get("main_group")
        sub_group = user_profile.get("sub_group")
        
        # Define a linha inicial para os botões de perfil
        next_row = 2
            
        # Lógica para o grupo 67 Telecom
        if main_group == "67_TELECOM":
            if sub_group in ["SUPER_ADMIN", "ADMIN"]:
                self.admin_button.grid(row=next_row, column=0, pady=8, padx=20)
                next_row += 1
            # Todos os utilizadores da 67 Telecom podem fazer registo detalhado
            self.partner_button.grid(row=next_row, column=0, pady=8, padx=20)
            next_row += 1

        # Lógica para o grupo Parceiros
        elif main_group == "PARTNER":
            self.partner_button.grid(row=next_row, column=0, pady=8, padx=20)
            next_row += 1

        # Lógica para o grupo Prefeitura
        elif main_group == "PREFEITURA":
            self.prefeitura_call_button.grid(row=next_row, column=0, pady=8, padx=20)
            next_row += 1
            self.prefeitura_equip_button.grid(row=next_row, column=0, pady=8, padx=20)
            next_row += 1
            
        # Botões comuns a todos os perfis
        self.history_button.grid(row=next_row, column=0, pady=8, padx=20)
        next_row += 1
        
        # Adiciona um espaçamento maior antes dos botões de saída
        self.logout_button.grid(row=next_row, column=0, pady=(20, 8), padx=20)
        next_row += 1
        
        self.exit_button.grid(row=next_row, column=0, pady=8, padx=20)
