# ==============================================================================
# FICHEIRO: src/views/admin_dashboard_view.py
# DESCRIÇÃO: Contém a classe de interface para o Dashboard de Gestão,
#            usado por administradores para gerir o sistema. (VERSÃO CORRIGIDA)
# ==============================================================================

import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
import json

class AdminDashboardView(ctk.CTkFrame):
    """Dashboard de gestão para administradores, organizado em abas."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.original_statuses = {}
        self.status_updaters = {}
        self.original_profiles = {}
        self.profile_updaters = {}
        
        self.partner_companies = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        occurrences_tab = self.tabview.add("Ocorrências")
        access_tab = self.tabview.add("Gerenciar Acessos")
        users_tab = self.tabview.add("Gerenciar Usuários")
        
        self.setup_occurrences_tab(occurrences_tab)
        self.setup_access_tab(access_tab)
        self.setup_users_tab(users_tab)
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def on_show(self):
        self.on_tab_change()

    def on_tab_change(self):
        selected_tab = self.tabview.get()
        if selected_tab == "Ocorrências": self.load_all_occurrences(force_refresh=True)
        elif selected_tab == "Gerenciar Acessos": self.load_access_requests()
        elif selected_tab == "Gerenciar Usuários": self.load_all_users(force_refresh=True)

    def setup_occurrences_tab(self, tab):
        ctk.CTkLabel(tab, text="Visão Geral de Todas as Ocorrências").pack(pady=5)
        self.all_occurrences_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...")
        self.all_occurrences_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes).pack(side="left", padx=(0, 10), expand=True, fill="x")
        ctk.CTkButton(button_frame, text="Atualizar Lista", command=lambda: self.load_all_occurrences(force_refresh=True)).pack(side="left", expand=True, fill="x")

    # --- CORREÇÃO AQUI: A função agora aceita o argumento 'force_refresh' ---
    def load_all_occurrences(self, force_refresh=False):
        self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
        threading.Thread(target=lambda: self.after(0, self._populate_all_occurrences, self.controller.get_all_occurrences(force_refresh)), daemon=True).start()

    def _populate_all_occurrences(self, all_occurrences_list):
        self.status_updaters.clear()
        self.original_statuses.clear()
        for widget in self.all_occurrences_frame.winfo_children(): widget.destroy()
        if not all_occurrences_list:
            self.all_occurrences_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
        self.all_occurrences_frame.configure(label_text="")
        status_options = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "RESOLVIDO", "CANCELADO"]
        for item in all_occurrences_list:
            item_id = item.get('ID', 'N/A')
            self.original_statuses[item_id] = item.get('Status', 'N/A')
            card = ctk.CTkFrame(self.all_occurrences_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            title = item.get('Título da Ocorrência', 'Ocorrência sem Título')
            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {item.get('Data de Registro', 'N/A')}", anchor="w", text_color="gray60").pack(anchor="w")
            
            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            status_combo = ctk.CTkComboBox(controls_frame, values=status_options, width=180)
            status_combo.set(self.original_statuses[item_id])
            status_combo.pack(side="left", padx=(0, 10))
            self.status_updaters[item_id] = status_combo
            ctk.CTkButton(controls_frame, text="Abrir", width=80, command=partial(self.controller.show_occurrence_details, item_id)).pack(side="left")

    def save_status_changes(self):
        changes = {occ_id: combo.get() for occ_id, combo in self.status_updaters.items() if self.original_statuses.get(occ_id) != combo.get()}
        self.controller.save_occurrence_status_changes(changes)

    def setup_access_tab(self, tab):
        ctk.CTkLabel(tab, text="Solicitações de Acesso Pendentes").pack(pady=5)
        self.pending_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...")
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        ctk.CTkButton(tab, text="Atualizar Lista", command=self.load_access_requests).pack(pady=5, padx=5, fill="x")

    def load_access_requests(self):
        self.pending_users_frame.configure(label_text="Carregando solicitações...")
        threading.Thread(target=lambda: self.after(0, self._populate_access_requests, self.controller.get_pending_requests()), daemon=True).start()

    def _populate_access_requests(self, pending_list):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame)
            card.pack(fill="x", pady=5)
            company_info = f" ({user.get('company')})" if user.get('company') else ""
            info_text = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\nE-mail: {user['email']}\nVínculo: {user['main_group']}{company_info}"
            ctk.CTkLabel(card, text=info_text, justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(card, text="Rejeitar", command=partial(self.controller.update_user_access, user['email'], 'rejected'), fg_color="red").pack(side="right", padx=5, pady=5)
            ctk.CTkButton(card, text="Aprovar", command=partial(self.controller.update_user_access, user['email'], 'approved'), fg_color="green").pack(side="right", padx=5, pady=5)

    def setup_users_tab(self, tab):
        ctk.CTkLabel(tab, text="Lista de Todos os Usuários").pack(pady=5)
        self.all_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...")
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(button_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes).pack(side="left", padx=(0, 10), expand=True, fill="x")
        ctk.CTkButton(button_frame, text="Atualizar Lista", command=lambda: self.load_all_users(force_refresh=True)).pack(side="left", expand=True, fill="x")

    # --- CORREÇÃO AQUI: A função agora aceita o argumento 'force_refresh' ---
    def load_all_users(self, force_refresh=False):
        self.all_users_frame.configure(label_text="Carregando usuários...")
        threading.Thread(target=lambda: self.after(0, self._populate_all_users, self.controller.get_all_users(force_refresh)), daemon=True).start()

    def _populate_all_users(self, all_users_list):
        self.profile_updaters.clear()
        self.original_profiles.clear()
        for widget in self.all_users_frame.winfo_children(): widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhum usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        main_group_options = ["67_TELECOM", "PARTNER", "PREFEITURA"]
        sub_group_options = ["SUPER_ADMIN", "ADMIN", "MANAGER", "USER"]
        
        for user in all_users_list:
            email = user.get('email')
            self.original_profiles[email] = {'main_group': user.get('main_group'), 'sub_group': user.get('sub_group'), 'company': user.get('company')}
            
            card = ctk.CTkFrame(self.all_users_frame)
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)
            
            info_text = f"{user.get('name', 'N/A')} (@{user.get('username', 'N/A')})"
            ctk.CTkLabel(card, text=info_text, anchor="w").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(card, text=email, anchor="w", text_color="gray60").grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")
            
            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="e")

            main_group_combo = ctk.CTkComboBox(controls_frame, values=main_group_options, width=140, command=partial(self._on_main_group_change, email))
            main_group_combo.set(user.get('main_group'))
            main_group_combo.pack(side="left", padx=(0, 5))

            sub_group_combo = ctk.CTkComboBox(controls_frame, values=sub_group_options, width=140)
            sub_group_combo.set(user.get('sub_group'))
            sub_group_combo.pack(side="left", padx=(0, 5))

            company_combo = ctk.CTkComboBox(controls_frame, values=[], width=180)
            company_combo.set(user.get('company', ''))
            
            self.profile_updaters[email] = {'main_group': main_group_combo, 'sub_group': sub_group_combo, 'company': company_combo}
            self._on_main_group_change(email, user.get('main_group'))

    def _on_main_group_change(self, email, selected_group):
        if self.profile_updaters.get(email, {}).get('company'):
            company_widget = self.profile_updaters[email]['company']
            
            if selected_group == 'PARTNER':
                company_widget.configure(values=self.partner_companies)
                if company_widget.get() not in self.partner_companies:
                    company_widget.set(self.partner_companies[0] if self.partner_companies else "")
                company_widget.pack(side="left")
            elif selected_group == 'PREFEITURA':
                company_widget.configure(values=self.prefeitura_dept_list)
                if company_widget.get() not in self.prefeitura_dept_list:
                    company_widget.set(self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")
                company_widget.pack(side="left")
            else:
                company_widget.pack_forget()

    def save_profile_changes(self):
        changes = {}
        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get()
            new_sub = widgets['sub_group'].get()
            new_comp = widgets['company'].get() if new_main in ['PARTNER', 'PREFEITURA'] else ""
            
            original = self.original_profiles.get(email, {})
            if original.get('main_group') != new_main or original.get('sub_group') != new_sub or original.get('company') != new_comp:
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}
        
        self.controller.update_user_profile(changes)
