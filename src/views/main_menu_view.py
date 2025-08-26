# ==============================================================================
# ARQUIVO: src/views/main_menu_view.py
# DESCRIÇÃO: Contém a classe de interface para o menu principal da aplicação REGTEL.
#            Exibe botões de ação dinamicamente com base no perfil do usuário logado.
#            ATUALIZADO para usar 'place()' para o layout principal.
# ==============================================================================

import customtkinter as ctk
from builtins import print, super

class MainMenuView(ctk.CTkFrame):
    """
    Menu principal da aplicação, com botões dinâmicos baseados no perfil do
    usuário logado. Controla quais funcionalidades o usuário pode acessar.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.title_label = ctk.CTkLabel(self, text="Menu Principal",
                                        font=ctk.CTkFont(size=28, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.place(relx=0.5, rely=0.1, anchor="n")

        self.buttons_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_container_frame.place(relx=0.5, rely=0.25, relwidth=0.5, relheight=0.6, anchor="n")

        ICON_DASHBOARD = "📊"
        ICON_CALL_DETAILED = "📞"
        ICON_CALL_SIMPLE = "☎️"
        ICON_EQUIPMENT = "⚙️"
        ICON_HISTORY = "📚"
        ICON_LOGOUT = "➡️"
        ICON_EXIT = "❌"

        self.admin_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_DASHBOARD} Dashboard de Gestão",
                                          command=lambda: self.controller.show_frame("AdminDashboardView"),
                                          height=45, width=350, font=ctk.CTkFont(size=14, weight="bold"),
                                          fg_color=self.controller.PRIMARY_COLOR,
                                          text_color=self.controller.TEXT_COLOR,
                                          hover_color=self.controller.ACCENT_COLOR,
                                          compound="left")

        self.partner_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_CALL_DETAILED} Registrar Ocorrência de Chamada (Detalhado)",
                                            command=lambda: self.controller.show_frame("RegistrationView"),
                                            height=45, width=350, font=ctk.CTkFont(size=14),
                                            fg_color=self.controller.PRIMARY_COLOR,
                                            text_color=self.controller.TEXT_COLOR,
                                            hover_color=self.controller.ACCENT_COLOR,
                                            compound="left")

        self.prefeitura_call_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_CALL_SIMPLE} Registrar Ocorrência de Chamada (Simplificado)",
                                                    command=lambda: self.controller.show_frame("SimpleCallView"),
                                                    height=45, width=350, font=ctk.CTkFont(size=14),
                                                    fg_color=self.controller.PRIMARY_COLOR,
                                                    text_color=self.controller.TEXT_COLOR,
                                                    hover_color=self.controller.ACCENT_COLOR,
                                                    compound="left")

        self.prefeitura_equip_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_EQUIPMENT} Registrar Suporte Técnico de Equipamento",
                                                     command=lambda: self.controller.show_frame("EquipmentView"),
                                                     height=45, width=350, font=ctk.CTkFont(size=14),
                                                     fg_color=self.controller.PRIMARY_COLOR,
                                                     text_color=self.controller.TEXT_COLOR,
                                                     hover_color=self.controller.ACCENT_COLOR,
                                                     compound="left")

        self.history_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_HISTORY} Ver Histórico de Ocorrências",
                                            command=lambda: self.controller.show_frame("HistoryView"),
                                            height=45, width=350, font=ctk.CTkFont(size=14),
                                            fg_color=self.controller.PRIMARY_COLOR,
                                            text_color=self.controller.TEXT_COLOR,
                                            hover_color=self.controller.ACCENT_COLOR,
                                            compound="left")

        self.logout_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_LOGOUT} Logout (Trocar de usuário)",
                                           command=self.controller.perform_logout,
                                           height=45, width=350, font=ctk.CTkFont(size=14),
                                           fg_color=self.controller.DANGER_COLOR,
                                           text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.DANGER_HOVER_COLOR,
                                           compound="left")

        self.exit_button = ctk.CTkButton(self.buttons_container_frame, text=f"{ICON_EXIT} Fechar Aplicação",
                                         command=self.controller.quit,
                                         height=45, width=350, font=ctk.CTkFont(size=14),
                                         fg_color=self.controller.GRAY_BUTTON_COLOR,
                                         text_color=self.controller.TEXT_COLOR,
                                         hover_color=self.controller.GRAY_HOVER_COLOR,
                                         compound="left")

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                         text_color="gray70")
        self.status_label.place(relx=0.5, rely=0.90, anchor="n")

        self.version_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10),
                                          text_color="gray50")
        self.version_label.place(relx=0.5, rely=0.95, anchor="n")

    def update_user_info(self, email, user_profile, app_version):
        """
        Atualiza a mensagem de boas-vindas, o e-mail do usuário logado e a versão da aplicação.
        Chama a função para exibir/esconder os botões de menu com base no perfil.
        :param email: E-mail do usuário logado.
        :param user_profile: Dicionário com os dados do perfil do usuário.
        :param app_version: A string da versão atual da aplicação.
        """
        username = user_profile.get("username", "")
        welcome_name = user_profile.get("name", username)
        self.title_label.configure(text=f"Bem-vindo, {welcome_name}!")
        self.status_label.configure(text=f"Login como: {email}")
        self.version_label.configure(text=f"Versão: {app_version}")
        self.update_buttons(user_profile)

    def update_buttons(self, user_profile):
        print(f"DEBUG: update_buttons chamado. Perfil do Usuário: {user_profile}")
        """
        Mostra ou esconde os botões de menu com base no perfil do usuário logado.
        :param user_profile: Dicionário com os dados do perfil do usuário.
        """
        for widget in self.buttons_container_frame.winfo_children():
            widget.pack_forget()

        main_group = user_profile.get("main_group")
        sub_group = user_profile.get("sub_group")
        print(f"DEBUG: main_group: {main_group}, sub_group: {sub_group}")

        if main_group == "67_TELECOM" and sub_group == "SUPER_ADMIN":
            self.title_label.configure(text=f"Menu Super Admin: {user_profile.get('name')}")
            self.admin_button.pack(pady=8, padx=20, fill="x")
            self.partner_button.pack(pady=8, padx=20, fill="x")
            self.prefeitura_call_button.pack(pady=8, padx=20, fill="x")
            self.prefeitura_equip_button.pack(pady=8, padx=20, fill="x")

        elif main_group == "67_TELECOM":
            if sub_group == "ADMIN":
                self.admin_button.pack(pady=8, padx=20, fill="x")
                self.partner_button.pack(pady=8, padx=20, fill="x")
            elif sub_group in ["MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"]:
                self.partner_button.pack(pady=8, padx=20, fill="x")

        elif main_group == "PARTNER":
            self.partner_button.pack(pady=8, padx=20, fill="x")

        elif main_group == "PREFEITURA":
            self.prefeitura_call_button.pack(pady=8, padx=20, fill="x")
            self.prefeitura_equip_button.pack(pady=8, padx=20, fill="x")

        self.history_button.pack(pady=8, padx=20, fill="x")
        self.logout_button.pack(pady=(20, 8), padx=20, fill="x")
        self.exit_button.pack(pady=8, padx=20, fill="x")
