# ==============================================================================
# FICHEIRO: src/views/user_management_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de Gerenciamento de Usuários,
#            onde administradores podem visualizar e editar perfis de utilizadores.
# ==============================================================================

import customtkinter as ctk
from functools import partial
import threading
from tkinter import messagebox
import json
from builtins import super, list, Exception, print, str, hasattr, len

class UserManagementView(ctk.CTkFrame):
    """
    Tela para administradores gerenciarem todos os utilizadores registados.
    Permite visualizar, filtrar e editar perfis de utilizadores.
    """
    def __init__(self, parent, controller):
        """
        Inicializa a UserManagementView.
        :param parent: O widget pai.
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        # Dicionários para armazenar o estado original e os widgets de atualização
        self.original_profiles = {}
        self.profile_updaters = {}

        # Listas de opções para ComboBoxes (copiadas do AdminDashboardView original)
        self.partner_companies = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]
        self.partner_subgroup_map = {
            "MDA FIBRA": "MDA_USER",
            "M2 TELECOMUNICAÇÕES": "M2_USER",
            "DISK SISTEMA TELECOM": "DISK_USER",
            "GMN TELECOM": "GMN_USER"
        }
        self.telecom_subgroups_for_admin = ["SUPER_ADMIN", "ADMIN", "MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"]


        self.grid_rowconfigure(2, weight=1) # Frame rolável
        self.grid_columnconfigure(0, weight=1)

        # Título da tela
        ctk.CTkLabel(self, text="Gerenciar Usuários",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # Frame de busca e filtros para usuários
        user_filter_frame = ctk.CTkFrame(self, fg_color="gray15")
        user_filter_frame.grid(row=1, column=0, fill="x", pady=(0, 10), padx=20)
        user_filter_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(user_filter_frame, text="Busca por Usuário:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_user_entry = ctk.CTkEntry(user_filter_frame, placeholder_text="Nome, e-mail ou username...",
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40")
        self.search_user_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.search_user_entry.bind("<KeyRelease>", self.filter_users_admin)

        # Frame rolável para exibir a lista de utilizadores
        self.all_users_frame = ctk.CTkScrollableFrame(self, label_text="Carregando usuários...",
                                                      fg_color="gray10",
                                                      label_text_color=self.controller.TEXT_COLOR)
        self.all_users_frame.grid(row=2, column=0, fill="both", expand=True, pady=10, padx=20)

        # Frame para os botões de ação
        user_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_buttons_frame.grid(row=3, column=0, fill="x", pady=(0, 10), padx=20)
        user_buttons_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(user_buttons_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(user_buttons_frame, text="Atualizar Lista de Usuários", command=lambda: self.load_all_users(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Botão para voltar ao dashboard
        ctk.CTkButton(self, text="Voltar ao Dashboard", command=lambda: self.controller.show_frame("AdminDashboardView"),
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=4, column=0, pady=(0, 10), padx=20, sticky="ew")


    def on_show(self):
        """
        Chamado sempre que esta tela é exibida.
        Carrega todos os utilizadores.
        """
        print("DEBUG: UserManagementView exibida. Carregando todos os usuários.")
        self.all_users_frame.configure(label_text="Carregando usuários...")
        self.update_idletasks()
        self.load_all_users(force_refresh=True)

    def filter_users_admin(self, event=None):
        """
        Filtra a lista de usuários exibida com base no termo de busca.
        :param event: O evento que acionou a filtragem (opcional).
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
        """
        Carrega todos os utilizadores e os popula na UI.
        Executado em uma thread separada para não bloquear a UI.
        :param force_refresh: Se True, força o recarregamento dos dados do Google Sheets.
        """
        print("DEBUG: Carregando todos os usuários para o dashboard.")
        threading.Thread(target=lambda: self.after(0, self._populate_all_users, self.controller.get_all_users(force_refresh)), daemon=True).start()

    def _populate_all_users(self, all_users_list):
        """
        Popula o frame rolável com os cards de todos os utilizadores.
        Permite a edição de grupo principal, subgrupo e empresa.
        :param all_users_list: Lista de dicionários, cada um representando um utilizador.
        """
        print("DEBUG: Populando lista de usuários na UI.")
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
            try:
                email = user.get('email', '')
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
                main_group_combo.set(original_main_group)
                main_group_combo.grid(row=0, column=0, padx=(0, 5), sticky="ew")

                sub_group_combo = ctk.CTkComboBox(controls_frame, values=[], width=140,
                                                  command=partial(self._on_sub_group_change, email),
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                  button_hover_color=self.controller.ACCENT_COLOR)
                sub_group_combo.set(original_sub_group)
                sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")

                company_combo = ctk.CTkComboBox(controls_frame, values=[], width=180,
                                                fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                button_hover_color=self.controller.ACCENT_COLOR)
                company_combo.set(original_company)
                company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew")

                self.profile_updaters[email] = {
                    'main_group': main_group_combo,
                    'sub_group': sub_group_combo,
                    'company': company_combo
                }
                self._on_main_group_change(email, original_main_group, initial_load=True)
            except Exception as e:
                print(f"ERRO ao popular card de usuário para {user.get('email', 'N/A')}: {e}")


    def _on_main_group_change(self, email, selected_main_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de subgrupo e empresa/departamento
        com base no grupo principal selecionado.
        :param email: E-mail do utilizador cujo perfil está a ser editado.
        :param selected_main_group: O novo grupo principal selecionado.
        :param initial_load: Booleano indicando se é o carregamento inicial do dashboard.
        """
        widgets = self.profile_updaters[email]
        sub_group_combo = widgets['sub_group']
        company_combo = widgets['company']
        
        selected_main_group = str(selected_main_group).strip().upper()

        sub_group_options = []
        if selected_main_group == 'PARTNER':
            sub_group_options = list(self.partner_subgroup_map.values())
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        elif selected_main_group == 'PREFEITURA':
            sub_group_options = ['PREFEITURA_USER']
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        elif selected_main_group == '67_TELECOM':
            sub_group_options = self.telecom_subgroups_for_admin
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        else:
            sub_group_combo.grid_forget()

        sub_group_combo.configure(values=sub_group_options)
        
        if initial_load and self.original_profiles[email]['sub_group'] in sub_group_options:
            sub_group_combo.set(self.original_profiles[email]['sub_group'])
        elif sub_group_options:
            sub_group_combo.set(sub_group_options[0])
        else:
            sub_group_combo.set("")

        _current_sub_group_value = sub_group_combo.get()
        self._on_sub_group_change(email, _current_sub_group_value, initial_load=initial_load)


    def _on_sub_group_change(self, email, selected_sub_group, initial_load=False):
        """
        Atualiza as opções do ComboBox de empresa/departamento
        com base no grupo principal e subgrupo selecionados.
        :param email: E-mail do utilizador cujo perfil está a ser editado.
        :param selected_sub_group: O novo subgrupo selecionado.
        :param initial_load: Booleano indicando se é o carregamento inicial do dashboard.
        """
        widgets = self.profile_updaters[email]
        main_group_combo = widgets['main_group']
        company_combo = widgets['company']
        
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
            company_combo.grid_forget()
            company_options = []
            company_to_set = "TRR"
        else:
            company_combo.grid_forget()
            company_options = []
            company_to_set = ""

        company_combo.configure(values=company_options)
        
        if initial_load and self.original_profiles[email]['company'] in company_options:
            company_combo.set(self.original_profiles[email]['company'])
        elif company_options:
            company_combo.set(company_options[0])
        else:
            company_combo.set(company_to_set)

    def save_profile_changes(self):
        """
        Coleta as alterações de perfil dos utilizadores e as envia para o controlador para salvamento em lote.
        Implementa lógica para garantir a consistência de main_group, sub_group e company.
        """
        changes = {}
        
        partner_subgroup_map = {
            "M2 TELECOMUNICAÇÕES": "M2_USER",
            "MDA FIBRA": "MDA_USER",
            "DISK SISTEMA TELECOM": "DISK_USER",
            "GMN TELECOM": "GMN_USER",
            "67 INTERNET": "67_INTERNET_USER" 
        }

        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get().strip()
            new_sub = widgets['sub_group'].get().strip()
            new_comp = widgets['company'].get().strip()
            
            if new_main == 'PARTNER':
                new_sub = partner_subgroup_map.get(new_comp, "USER")
            elif new_main == 'PREFEITURA':
                new_sub = "PREFEITURA_USER"
            elif new_main == '67_TELECOM':
                new_comp = "TRR"

            original = self.original_profiles.get(email, {})
            
            if original.get('main_group') != new_main or original.get('sub_group') != new_sub or original.get('company') != new_comp:
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}

        if changes:
            self.controller.update_user_profile(changes)
        else:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")

