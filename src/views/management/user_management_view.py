# ==============================================================================
# ARQUIVO: src/views/user_management_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de Gerenciamento de Usuários.
#            (VERSÃO OTIMIZADA PARA CARREGAMENTO EM SEGUNDO PLANO)
# ==============================================================================

import customtkinter as ctk
from functools import partial
import threading
from tkinter import messagebox
import json
from builtins import super, list, Exception, print, str, hasattr, len

class UserManagementView(ctk.CTkFrame):
    """
    Tela para administradores gerenciarem todos os usuários registrados.
    Permite visualizar, filtrar e editar perfis de usuários.
    """
    def __init__(self, parent, controller):
        """
        Inicializa a tela de Gerenciamento de Usuários.

        :param parent: O widget pai (geralmente a instância da classe App).
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        # Dicionários para armazenar o estado original dos perfis e os widgets de edição
        self.original_profiles = {}
        self.profile_updaters = {}

        # Listas de opções para os ComboBoxes de seleção de perfil
        self.partner_companies = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]
        self.partner_subgroup_map = {
            "MDA FIBRA": "MDA_USER",
            "M2 TELECOMUNICAÇÕES": "M2_USER",
            "DISK SISTEMA TELECOM": "DISK_USER",
            "GMN TELECOM": "GMN_USER"
        }
        self.telecom_subgroups_for_admin = ["SUPER_ADMIN", "ADMIN", "MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"]

        # --- Layout Principal em Grid ---
        self.grid_rowconfigure(2, weight=1)  # Linha do frame rolável expande
        self.grid_columnconfigure(0, weight=1)

        # Título da tela
        ctk.CTkLabel(self, text="Gerenciar Usuários",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # --- Frame de Filtro e Busca ---
        user_filter_frame = ctk.CTkFrame(self, fg_color="gray15")
        user_filter_frame.grid(row=1, column=0, pady=(0, 10), padx=20, sticky="ew")
        user_filter_frame.grid_columnconfigure(0, weight=1)
        self.search_user_entry = ctk.CTkEntry(user_filter_frame, placeholder_text="Nome, e-mail ou nome de usuário...")
        self.search_user_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.search_user_entry.bind("<KeyRelease>", self.filter_users_admin)

        # --- Frame Rolável para a Lista de Usuários ---
        self.all_users_frame = ctk.CTkScrollableFrame(self, label_text="Carregando usuários...")
        self.all_users_frame.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")

        # --- Botões de Ação ---
        user_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_buttons_frame.grid(row=3, column=0, pady=(0, 10), padx=20, sticky="ew")
        user_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(user_buttons_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(user_buttons_frame, text="Atualizar Lista", command=lambda: self.load_all_users(force_refresh=True)).grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkButton(self, text="Voltar ao Dashboard", command=lambda: self.controller.show_frame("AdminDashboardView")).grid(row=4, column=0, pady=10, padx=20, sticky="ew")

    def on_show(self):
        """
        Método chamado sempre que a tela é exibida.
        Inicia o carregamento forçado dos dados dos usuários.
        """
        self.load_all_users(force_refresh=True)

    def filter_users_admin(self, event=None):
        """
        Filtra a lista de usuários exibida na tela com base no texto digitado
        no campo de busca. A filtragem ocorre localmente, usando o cache de usuários.
        """
        search_term = self.search_user_entry.get().lower()
        all_users = self.controller.get_all_users() 
        if not all_users:
            all_users = []
        # Filtra a lista de usuários buscando o termo de pesquisa no nome, e-mail ou nome de usuário
        filtered_users = [u for u in all_users if search_term in u.get('name','').lower() or search_term in u.get('email','').lower() or search_term in u.get('username','').lower()]
        self._populate_all_users(filtered_users)

    def load_all_users(self, force_refresh=False):
        """
        Inicia o processo de carregamento dos usuários em uma thread separada
        para não bloquear a interface gráfica.
        
        :param force_refresh: Se True, força a busca dos dados da planilha, ignorando o cache.
        """
        self.all_users_frame.configure(label_text="Carregando usuários...")
        # Limpa a lista de usuários existente antes de carregar a nova
        for widget in self.all_users_frame.winfo_children():
            widget.destroy()
        self.update_idletasks() # Força a atualização da UI para exibir a mensagem de carregamento
        # Inicia a thread para buscar os dados em segundo plano
        threading.Thread(target=self._load_users_thread, args=(force_refresh,), daemon=True).start()

    def _load_users_thread(self, force_refresh):
        """
        Método executado na thread secundária para buscar a lista de usuários.
        Após a busca, agenda a atualização da interface na thread principal.
        
        :param force_refresh: Passado para a função de busca de dados.
        """
        all_users_list = self.controller.get_all_users(force_refresh)
        # Agenda a chamada ao método _populate_all_users na thread principal
        self.after(0, self._populate_all_users, all_users_list)

    def _populate_all_users(self, all_users_list):
        """
        Popula a interface com os cards de cada usuário, incluindo os
        controles para edição de perfil (ComboBoxes).
        
        :param all_users_list: A lista de dicionários de usuários a ser exibida.
        """
        self.profile_updaters.clear()
        self.original_profiles.clear()
        for widget in self.all_users_frame.winfo_children():
            widget.destroy()

        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhum usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        
        main_group_options = ["67_TELECOM", "PARTNER", "PREFEITURA"]
        
        for user in all_users_list:
            email = user.get('email', '')
            if not email: continue

            # Armazena o perfil original para comparar com as edições
            original_main_group = user.get('main_group', '')
            original_sub_group = user.get('sub_group', '')
            original_company = user.get('company', '')

            self.original_profiles[email] = {
                'main_group': original_main_group,
                'sub_group': original_sub_group,
                'company': original_company
            }

            # Cria um card para cada usuário
            card = ctk.CTkFrame(self.all_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5, padx=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=2)

            # Informações do usuário
            info_text = f"{user.get('name', 'N/A')} (@{user.get('username', 'N/A')})"
            ctk.CTkLabel(card, text=info_text, anchor="w").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(card, text=email, anchor="w", text_color="gray60").grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

            # Controles de edição do perfil
            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid_columnconfigure((0, 1, 2), weight=1)
            controls_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="nsew")

            main_group_combo = ctk.CTkComboBox(controls_frame, values=main_group_options, command=partial(self._on_main_group_change, email))
            main_group_combo.set(original_main_group)
            main_group_combo.grid(row=0, column=0, padx=(0, 5), sticky="ew")

            sub_group_combo = ctk.CTkComboBox(controls_frame, values=[], command=partial(self._on_sub_group_change, email))
            sub_group_combo.set(original_sub_group)
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")

            company_combo = ctk.CTkComboBox(controls_frame, values=[])
            company_combo.set(original_company)
            company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew")

            # Armazena os widgets de edição para coletar os dados ao salvar
            self.profile_updaters[email] = {
                'main_group': main_group_combo,
                'sub_group': sub_group_combo,
                'company': company_combo
            }
            # Inicializa os valores dos ComboBoxes dependentes
            self._on_main_group_change(email, original_main_group, initial_load=True)

    def _on_main_group_change(self, email, selected_main_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de subgrupo com base no grupo principal selecionado.
        
        :param email: O e-mail do usuário sendo editado.
        :param selected_main_group: O grupo principal selecionado.
        :param initial_load: Flag para indicar se é o carregamento inicial do card.
        """
        widgets = self.profile_updaters[email]
        sub_group_combo = widgets['sub_group']
        
        sub_group_options = []
        if selected_main_group == 'PARTNER':
            sub_group_options = list(self.partner_subgroup_map.values())
        elif selected_main_group == 'PREFEITURA':
            sub_group_options = ['PREFEITURA_USER']
        elif selected_main_group == '67_TELECOM':
            sub_group_options = self.telecom_subgroups_for_admin
        
        sub_group_combo.configure(values=sub_group_options)
        
        # Define o valor do ComboBox
        if initial_load and self.original_profiles[email]['sub_group'] in sub_group_options:
            sub_group_combo.set(self.original_profiles[email]['sub_group'])
        elif sub_group_options:
            sub_group_combo.set(sub_group_options[0])
        else:
            sub_group_combo.set("")

        # Chama a atualização do próximo ComboBox dependente
        self._on_sub_group_change(email, sub_group_combo.get(), initial_load=initial_load)

    def _on_sub_group_change(self, email, selected_sub_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de empresa/departamento com base no grupo principal.
        
        :param email: O e-mail do usuário sendo editado.
        :param selected_sub_group: O subgrupo selecionado (usado indiretamente).
        :param initial_load: Flag para indicar se é o carregamento inicial do card.
        """
        widgets = self.profile_updaters[email]
        main_group_combo = widgets['main_group']
        company_combo = widgets['company']
        
        selected_main_group = main_group_combo.get()
        
        company_options = []
        company_to_set = ""

        if selected_main_group == 'PARTNER':
            company_options = self.partner_companies
        elif selected_main_group == 'PREFEITURA':
            company_options = self.prefeitura_dept_list
        elif selected_main_group == '67_TELECOM':
            company_to_set = "TRR"
        
        company_combo.configure(values=company_options)
        
        # Define o valor do ComboBox
        if initial_load and self.original_profiles[email]['company'] in company_options:
            company_combo.set(self.original_profiles[email]['company'])
        elif company_options:
            company_combo.set(company_options[0])
        else:
            company_combo.set(company_to_set)

    def save_profile_changes(self):
        """
        Coleta todas as alterações de perfil feitas na tela, compara com os
        valores originais e envia um dicionário de 'changes' para o controlador
        para serem salvas em lote.
        """
        changes = {}
        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get().strip()
            new_sub = widgets['sub_group'].get().strip()
            new_comp = widgets['company'].get().strip()

            # Aplica regras de negócio para garantir consistência
            if new_main == 'PARTNER':
                new_sub = self.partner_subgroup_map.get(new_comp, "USER")
            elif new_main == 'PREFEITURA':
                new_sub = "PREFEITURA_USER"
            elif new_main == '67_TELECOM':
                new_comp = "TRR"

            original = self.original_profiles.get(email, {})
            
            # Verifica se houve alguma alteração no perfil
            if (original.get('main_group') != new_main or 
                original.get('sub_group') != new_sub or 
                original.get('company') != new_comp):
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}

        if changes:
            self.controller.update_user_profile(changes)
        else:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")
