# ==============================================================================
# FICHEIRO: src/views/admin_dashboard_view.py
# DESCRIÇÃO: Contém a classe de interface para o Dashboard de Gestão,
#            usado por administradores para gerir o sistema. (VERSÃO OTIMIZADA PARA CARREGAMENTO E LAYOUT)
# ==============================================================================

import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
import json
from datetime import datetime # Importação adicionada para validação de data
import re # Importação adicionada para validação de data
from builtins import super, list, Exception, print, str # CORRIGIDO: Importa built-ins explicitamente para satisfazer o Pylance

class AdminDashboardView(ctk.CTkFrame):
    """Dashboard de gestão para administradores, organizado em abas."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        # Garantir que o frame principal expanda
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.original_statuses = {}
        self.status_updaters = {}
        self.original_profiles = {}
        self.profile_updaters = {}

        # CORREÇÃO 1: Remover "67 INTERNET" das empresas parceiras
        self.partner_companies = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]
        
        # CORREÇÃO 1: Remover "67 INTERNET" do mapeamento de subgrupos para parceiros
        self.partner_subgroup_map = {
            "MDA FIBRA": "MDA_USER",
            "M2 TELECOMUNICAÇÕES": "M2_USER",
            "DISK SISTEMA TELECOM": "DISK_USER",
            "GMN TELECOM": "GMN_USER"
        }
        # Subgrupos para 67_TELECOM (visíveis no admin)
        self.telecom_subgroups_for_admin = ["SUPER_ADMIN", "ADMIN", "MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"]


        ctk.CTkLabel(self, text="Dashboard de Gestão",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change,
                                      fg_color="gray15",
                                      segmented_button_fg_color=self.controller.PRIMARY_COLOR,
                                      segmented_button_selected_color=self.controller.ACCENT_COLOR,
                                      segmented_button_unselected_color="gray30",
                                      segmented_button_selected_hover_color=self.controller.ACCENT_COLOR,
                                      segmented_button_unselected_hover_color="gray25",
                                      text_color=self.controller.TEXT_COLOR)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # REMOVIDO: Acesso direto a atributos internos como _segmented_button e _tabview
        # A configuração de expansão para o conteúdo das abas será feita nos métodos setup_X_tab.

        self.occurrences_tab = self.tabview.add("Ocorrências")
        self.access_tab = self.tabview.add("Gerenciar Acessos")
        self.users_tab = self.tabview.add("Gerenciar Usuários")

        # Configurar expansão das abas (para que o conteúdo dentro delas possa expandir)
        # Estes grid_rowconfigure e grid_columnconfigure devem ser para o conteúdo dentro da aba,
        # e serão definidos nos métodos setup_X_tab.
        # Removido daqui para evitar duplicação e garantir que são aplicados no momento certo.

        self._occurrences_tab_initialized = False
        self._access_tab_initialized = False
        self._users_tab_initialized = False

        back_button = ctk.CTkButton(self, text="Voltar ao Menu",
                                    command=lambda: self.controller.show_frame("MainMenuView"),
                                    fg_color=self.controller.GRAY_BUTTON_COLOR,
                                    text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def on_show(self):
        print("DEBUG: AdminDashboardView exibida. Inicializando abas...")
        
        # Inicializar todas as abas ao exibir o dashboard se ainda não o foram
        if not self._occurrences_tab_initialized:
            self.setup_occurrences_tab(self.occurrences_tab)
            self._occurrences_tab_initialized = True
        
        if not self._access_tab_initialized:
            self.setup_access_tab(self.access_tab)
            self._access_tab_initialized = True
        
        if not self._users_tab_initialized:
            self.setup_users_tab(self.users_tab)
            self._users_tab_initialized = True

        # Carregar dados para todas as abas (ou pelo menos iniciar o carregamento e definir mensagens)
        # Assegurar que os frames scrollable existem antes de configurar o label_text
        if hasattr(self, 'all_occurrences_frame'):
            self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
        if hasattr(self, 'pending_users_frame'):
            self.pending_users_frame.configure(label_text="Carregando solicitações...")
        if hasattr(self, 'all_users_frame'):
            self.all_users_frame.configure(label_text="Carregando usuários...")
        self.update_idletasks() # Força a atualização da UI para mostrar as mensagens de carregamento

        # Iniciar o carregamento de dados para todas as abas em paralelo
        self.load_all_occurrences(force_refresh=True)
        self.load_access_requests()
        self.load_all_users(force_refresh=True)

        self.tabview.set("Ocorrências") # Focar na aba padrão
        print("DEBUG: Inicialização de abas concluída e dados carregados.")


    def on_tab_change(self, selected_tab=None):
        print(f"DEBUG: Aba alterada para: {selected_tab}")
        if selected_tab is None:
            selected_tab = self.tabview.get()

        # A lógica de on_tab_change agora pode ser mais simples, pois on_show já inicializa tudo
        # Mas mantemos a chamada de load_X_requests/users para garantir que os dados sejam sempre os mais recentes
        # quando o usuário troca de aba, mesmo que a aba já esteja inicializada.
        if selected_tab == "Ocorrências":
            if hasattr(self, 'all_occurrences_frame'):
                self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
            self.update_idletasks()
            self.load_all_occurrences(force_refresh=True)
        elif selected_tab == "Gerenciar Acessos":
            if hasattr(self, 'pending_users_frame'):
                self.pending_users_frame.configure(label_text="Carregando solicitações...")
            self.update_idletasks()
            self.load_access_requests()
        elif selected_tab == "Gerenciar Usuários":
            if hasattr(self, 'all_users_frame'):
                self.all_users_frame.configure(label_text="Carregando usuários...")
            self.update_idletasks()
            self.load_all_users(force_refresh=True)

    def setup_occurrences_tab(self, tab):
        print("DEBUG: Configurando aba de Ocorrências.")
        # Configurar expansão da aba para o seu conteúdo
        tab.grid_rowconfigure(0, weight=0) # Título
        tab.grid_rowconfigure(1, weight=0) # Frame de Filtros
        tab.grid_rowconfigure(2, weight=1) # all_occurrences_frame (Scrollable Frame)
        tab.grid_rowconfigure(3, weight=0) # Botões de ação
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Visão Geral de Todas as Ocorrências", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, pady=5, sticky="w")

        # Frame de Filtros e Busca (similar ao HistoryView)
        filter_frame = ctk.CTkFrame(tab, fg_color="gray15")
        filter_frame.grid(row=1, column=0, fill="x", pady=(0, 10), padx=5)
        filter_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) # Ajuste conforme layout

        ctk.CTkLabel(filter_frame, text="Painel de Filtros",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...",
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40")
        self.search_entry_admin.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filtrar por Status:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        status_options = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
        status_options_admin = ["TODOS"] + status_options # Inclui o novo status
        self.status_filter_admin = ctk.CTkComboBox(filter_frame, values=status_options_admin,
                                                   fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                   border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                   button_hover_color=self.controller.ACCENT_COLOR)
        self.status_filter_admin.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter_admin.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options_admin = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter_admin = ctk.CTkComboBox(filter_frame, values=type_options_admin,
                                                 fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                 border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                 button_hover_color=self.controller.ACCENT_COLOR)
        self.type_filter_admin.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter_admin.set("TODOS")

        # Datas
        ctk.CTkLabel(filter_frame, text="Data de Início (DD-MM-AAAA):", text_color=self.controller.TEXT_COLOR).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40")
        self.start_date_entry_admin.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.start_date_entry_admin.bind("<KeyRelease>", partial(self._validate_date_live_admin, self.start_date_entry_admin))
        self.start_date_entry_admin.bind("<FocusOut>", partial(self._validate_date_live_admin, self.start_date_entry_admin, is_focus_out=True))

        ctk.CTkLabel(filter_frame, text="Data de Fim (DD-MM-AAAA):", text_color=self.controller.TEXT_COLOR).grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40")
        self.end_date_entry_admin.grid(row=4, column=1, sticky="ew", padx=10, pady=(0, 10))
        self.end_date_entry_admin.bind("<KeyRelease>", partial(self._validate_date_live_admin, self.end_date_entry_admin))
        self.end_date_entry_admin.bind("<FocusOut>", partial(self._validate_date_live_admin, self.end_date_entry_admin, is_focus_out=True))
        self.default_border_color_admin = self.search_entry_admin.cget("border_color")


        button_frame_filters = ctk.CTkFrame(filter_frame, fg_color="transparent")
        # ALTERAÇÃO: Configura 3 colunas para distribuir o espaço igualmente
        button_frame_filters.grid(row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        button_frame_filters.grid_columnconfigure((0, 1, 2), weight=1) # Adicionado weight para a 3ª coluna

        self.apply_filters_button_admin = ctk.CTkButton(button_frame_filters, text="Aplicar Filtros", command=self.filter_occurrences_admin,
                                                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                                      hover_color=self.controller.ACCENT_COLOR)
        self.apply_filters_button_admin.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_filters_button_admin = ctk.CTkButton(button_frame_filters, text="Limpar Filtros", command=self.clear_filters_admin,
                                                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                                      hover_color=self.controller.GRAY_HOVER_COLOR)
        self.clear_filters_button_admin.grid(row=0, column=1, padx=(5, 5), sticky="ew") # Ajustado padx

        # NOVO POSICIONAMENTO: Botão "Ir para Histórico"
        ctk.CTkButton(button_frame_filters, text="Ir para Histórico",
                      # ATUALIZAÇÃO: Passe o nome da tela atual como from_view
                      command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView"),
                      fg_color=self.controller.PRIMARY_COLOR, # Pode ser outra cor se preferir
                      text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=2, padx=(5, 0), sticky="ew") # Nova coluna


        self.all_occurrences_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...",
                                                           fg_color="gray10",
                                                           label_text_color=self.controller.TEXT_COLOR)
        self.all_occurrences_frame.grid(row=2, column=0, fill="both", expand=True, pady=5, padx=5)

        # Frame inferior, agora sem o botão "Ir para Histórico"
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=3, column=0, fill="x", pady=5, padx=5)
        button_frame.grid_columnconfigure((0, 1), weight=1) # Ajustado para 2 colunas

        ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(button_frame, text="Atualizar Lista", command=lambda: self.load_all_occurrences(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=0, column=1, padx=(5, 0), sticky="ew")


    def setup_access_tab(self, tab):
        print("DEBUG: Configurando aba de Gerenciar Acessos.")
        # Configurar expansão da aba para o seu conteúdo
        tab.grid_rowconfigure(0, weight=0) # Título
        tab.grid_rowconfigure(1, weight=1) # pending_users_frame (Scrollable Frame)
        tab.grid_rowconfigure(2, weight=0) # Botão de atualizar
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Solicitações de Acesso Pendentes", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, pady=5, sticky="w")
        self.pending_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando solicitações...",
                                                          fg_color="gray10",
                                                          label_text_color=self.controller.TEXT_COLOR)
        self.pending_users_frame.grid(row=1, column=0, fill="both", expand=True, pady=5, padx=5)

        ctk.CTkButton(tab, text="Atualizar Lista", command=self.load_access_requests,
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=2, column=0, pady=5, padx=5, fill="x")

    def load_access_requests(self):
        print("DEBUG: Carregando solicitações de acesso pendentes.")
        threading.Thread(target=lambda: self.after(0, self._populate_access_requests, self.controller.get_pending_requests()), daemon=True).start()

    def _populate_access_requests(self, pending_list):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)

            company_info = f" ({user.get('company')})" if user.get('company') else ""
            info_text = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\n" \
                        f"E-mail: {user['email']}\nVínculo: {user['main_group']}{company_info}"

            ctk.CTkLabel(card, text=info_text, justify="left",
                         text_color=self.controller.TEXT_COLOR).pack(side="left", padx=10, pady=5)

            ctk.CTkButton(card, text="Rejeitar",
                          command=partial(self.controller.update_user_access, user['email'], 'rejected'),
                          fg_color=self.controller.DANGER_COLOR, text_color=self.controller.TEXT_COLOR,
                          hover_color=self.controller.DANGER_HOVER_COLOR).pack(side="right", padx=5, pady=5)

            ctk.CTkButton(card, text="Aprovar",
                          command=partial(self.controller.update_user_access, user['email'], 'approved'),
                          fg_color="green",
                          text_color=self.controller.TEXT_COLOR,
                          hover_color="darkgreen").pack(side="right", padx=5, pady=5)

    def save_profile_changes(self):
        changes = {}
        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get()
            new_sub = widgets['sub_group'].get()
            
            # Lógica para determinar new_comp com base no main_group e sub_group
            new_comp = ""
            if new_main == 'PARTNER':
                # Para parceiros, a empresa é a selecionada diretamente
                new_comp = widgets['company'].get()
            elif new_main == 'PREFEITURA':
                # Para prefeitura, a empresa é a selecionada diretamente
                new_comp = widgets['company'].get()
            elif new_main == '67_TELECOM':
                # CORREÇÃO 2: Para 67_TELECOM a empresa é SEMPRE TRR, independentemente do subgrupo
                new_comp = "TRR"

            original = self.original_profiles.get(email, {})
            if original.get('main_group') != new_main or original.get('sub_group') != new_sub or original.get('company') != new_comp:
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}

        self.controller.update_user_profile(changes)

    def setup_users_tab(self, tab):
        print("DEBUG: Configurando aba de Gerenciar Usuários.")
        # Configurar expansão da aba para o seu conteúdo
        tab.grid_rowconfigure(0, weight=0) # Título
        tab.grid_rowconfigure(1, weight=0) # Frame de filtro
        tab.grid_rowconfigure(2, weight=1) # all_users_frame (Scrollable Frame)
        tab.grid_rowconfigure(3, weight=0) # Botões de ação
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Lista de Todos os Usuários", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, pady=5, sticky="w")

        # Frame de busca e filtros para usuários
        user_filter_frame = ctk.CTkFrame(tab, fg_color="gray15")
        user_filter_frame.grid(row=1, column=0, fill="x", pady=(0, 10), padx=5)
        user_filter_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(user_filter_frame, text="Busca por Usuário:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_user_entry = ctk.CTkEntry(user_filter_frame, placeholder_text="Nome, e-mail ou username...",
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40")
        self.search_user_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.search_user_entry.bind("<KeyRelease>", self.filter_users_admin)


        self.all_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando usuários...",
                                                      fg_color="gray10",
                                                      label_text_color=self.controller.TEXT_COLOR)
        self.all_users_frame.grid(row=2, column=0, fill="both", expand=True, pady=5, padx=5)

        # Frame para os botões de ação na aba de Usuários
        user_buttons_frame = ctk.CTkFrame(tab, fg_color="transparent")
        user_buttons_frame.grid(row=3, column=0, fill="x", pady=5, padx=5)
        user_buttons_frame.grid_columnconfigure((0, 1), weight=1) # Configura para duas colunas de peso igual

        # Botão "Salvar Alterações de Perfil"
        ctk.CTkButton(user_buttons_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # Botão "Atualizar Lista de Usuários"
        ctk.CTkButton(user_buttons_frame, text="Atualizar Lista de Usuários", command=lambda: self.load_all_users(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def filter_users_admin(self, event=None):
        """
        Filtra a lista de usuários exibida com base no termo de busca.
        """
        search_term = self.search_user_entry.get().lower()
        all_users = self.controller.get_all_users() # Obtém todos os usuários (pode ser do cache)

        if not search_term:
            filtered_users = all_users
        else:
            filtered_users = [
                user for user in all_users
                if search_term in user.get('name', '').lower() or
                   search_term in user.get('email', '').lower() or
                   search_term in user.get('username', '').lower()
            ]
        self._populate_all_users(filtered_users)


    def load_all_users(self, force_refresh=False):
        print("DEBUG: Carregando todos os usuários para o dashboard.")
        # Carrega todos os usuários e os popula na UI.
        threading.Thread(target=lambda: self.after(0, self._populate_all_users, self.controller.get_all_users(force_refresh)), daemon=True).start()

    def _populate_all_users(self, all_users_list):
        print("DEBUG: Populando lista de usuários na UI.")
        self.profile_updaters.clear()
        self.original_profiles.clear()
        for widget in self.all_users_frame.winfo_children(): widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhum usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        
        main_group_options = ["67_TELECOM", "PARTNER", "PREFEITURA"]
        
        for user in all_users_list:
            try: # Adicionado try-except para cada card de usuário
                email = user.get('email', '') # Garante que email é uma string
                # Pega os valores originais com fallback para string vazia
                original_main_group = user.get('main_group', '')
                original_sub_group = user.get('sub_group', '')
                original_company = user.get('company', '')

                self.original_profiles[email] = {
                    'main_group': original_main_group,
                    'sub_group': original_sub_group,
                    'company': original_company
                }

                card = ctk.CTkFrame(self.all_users_frame, fg_color="gray20")
                card.pack(fill="x", pady=5)
                card.grid_columnconfigure(0, weight=1)

                info_text = f"{user.get('name', 'N/A')} (@{user.get('username', 'N/A')})"
                ctk.CTkLabel(card, text=info_text, anchor="w", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(card, text=email, anchor="w", text_color="gray60").grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

                controls_frame = ctk.CTkFrame(card, fg_color="transparent")
                controls_frame.grid_columnconfigure((0, 1, 2), weight=1)
                controls_frame.grid_rowconfigure(0, weight=1)
                controls_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="nsew")

                main_group_combo = ctk.CTkComboBox(controls_frame, values=main_group_options, width=140,
                                                   command=partial(self._on_main_group_change, email),
                                                   fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                   border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                   button_hover_color=self.controller.ACCENT_COLOR)
                main_group_combo.set(original_main_group) # Define o valor original
                main_group_combo.grid(row=0, column=0, padx=(0, 5), sticky="ew")

                sub_group_combo = ctk.CTkComboBox(controls_frame, values=[], width=140,
                                                  command=partial(self._on_sub_group_change, email),
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                  button_hover_color=self.controller.ACCENT_COLOR)
                sub_group_combo.set(original_sub_group) # Define o valor original
                sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")

                company_combo = ctk.CTkComboBox(controls_frame, values=[], width=180,
                                                fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                button_hover_color=self.controller.ACCENT_COLOR)
                company_combo.set(original_company) # Define o valor original
                company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew")

                self.profile_updaters[email] = {
                    'main_group': main_group_combo,
                    'sub_group': sub_group_combo,
                    'company': company_combo
                }
                # Chama a função de mudança de grupo principal para inicializar os subgrupos e empresa
                self._on_main_group_change(email, original_main_group, initial_load=True)
            except Exception as e:
                print(f"ERRO ao popular card de usuário para {user.get('email', 'N/A')}: {e}")
                # Opcional: Adicionar um label de erro no scrollable frame para este card específico.


    def _on_main_group_change(self, email, selected_main_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de subgrupo e empresa/departamento
        com base no grupo principal selecionado.
        """
        widgets = self.profile_updaters[email]
        sub_group_combo = widgets['sub_group']
        company_combo = widgets['company']
        
        # Garante que selected_main_group é uma string para evitar erros de None
        selected_main_group = str(selected_main_group).strip().upper()

        # --- Atualiza as opções do ComboBox de Subgrupo ---
        sub_group_options = []
        if selected_main_group == 'PARTNER':
            sub_group_options = list(self.partner_subgroup_map.values())
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew") # Garante que está visível
        elif selected_main_group == 'PREFEITURA':
            sub_group_options = ['PREFEITURA_USER']
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew") # Garante que está visível
        elif selected_main_group == '67_TELECOM':
            sub_group_options = self.telecom_subgroups_for_admin
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew") # Garante que está visível
        else:
            sub_group_combo.grid_forget() # Esconde o ComboBox de subgrupo

        sub_group_combo.configure(values=sub_group_options)
        
        # Tenta definir o valor original ou o primeiro da lista, se disponível
        if initial_load and self.original_profiles[email]['sub_group'] in sub_group_options:
            sub_group_combo.set(self.original_profiles[email]['sub_group'])
        elif sub_group_options:
            sub_group_combo.set(sub_group_options[0])
        else:
            sub_group_combo.set("") # Limpa se não houver opções

        # Chama a função de mudança de subgrupo para atualizar o ComboBox da empresa
        # Passa initial_load para que a lógica de empresa também possa usar o valor original
        self._on_sub_group_change(email, sub_group_combo.get(), initial_load=initial_load)


    def _on_sub_group_change(self, email, selected_sub_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de empresa/departamento
        com base no grupo principal e subgrupo selecionados.
        """
        widgets = self.profile_updaters[email]
        main_group_combo = widgets['main_group']
        company_combo = widgets['company']
        
        # Garante que selected_main_group e selected_sub_group são strings
        selected_main_group = str(main_group_combo.get()).strip().upper()
        selected_sub_group = str(selected_sub_group).strip().upper()
        
        company_options = []
        company_to_set = ""

        if selected_main_group == 'PARTNER':
            company_options = self.partner_companies
            company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew")
        elif selected_main_group == 'PREFEITURA':
            company_options = self.prefeitura_dept_list
            company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew")
        elif selected_main_group == '67_TELECOM':
            # CORREÇÃO 3: Sempre ocultar o combo e definir TRR, independentemente do subgrupo
            company_combo.grid_forget() # Esconde a empresa
            company_options = [] # Limpa as opções
            company_to_set = "TRR" # Define TRR como valor lógico
        else:
            company_combo.grid_forget()
            company_options = []
            company_to_set = ""

        company_combo.configure(values=company_options)
        
        # Tenta definir o valor original ou o primeiro da lista, se disponível
        if initial_load and self.original_profiles[email]['company'] in company_options:
            company_combo.set(self.original_profiles[email]['company'])
        elif company_options:
            company_combo.set(company_options[0])
        else:
            company_combo.set(company_to_set) # Fallback para o valor lógico (TRR) ou vazio
