import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
import json

class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.original_statuses = {}
        self.status_updaters = {}
        self.original_profiles = {} # Guarda perfil e empresa
        self.profile_updaters = {} # Guarda os widgets de perfil e empresa
        self.partner_companies = []
        self.current_analysis_list = []

        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.occurrences_tab = self.tabview.add("Ocorrências")
        self.analysis_tab = self.tabview.add("Análise de Dados")
        self.access_tab = self.tabview.add("Gerenciar Acessos")
        self.users_tab = self.tabview.add("Gerenciar Usuários")
        
        self.setup_occurrences_tab()
        self.setup_analysis_tab()
        self.setup_access_tab()
        self.setup_users_tab()
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def setup_users_tab(self):
        ctk.CTkLabel(self.users_tab, text="Lista de Todos os Usuários").pack(pady=5)
        self.all_users_frame = ctk.CTkScrollableFrame(self.users_tab, label_text="Carregando...")
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.users_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        save_button = ctk.CTkButton(button_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes)
        save_button.pack(side="left", padx=(0, 10), expand=True, fill="x")
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Lista", command=self.load_all_users)
        refresh_button.pack(side="left", expand=True, fill="x")

    def load_all_users(self):
        self.all_users_frame.configure(label_text="Carregando usuários...")
        threading.Thread(target=self._load_users_data_thread, daemon=True).start()

    def _load_users_data_thread(self):
        all_users_list = self.controller.get_all_users()
        self.partner_companies = self.controller.get_partner_companies()
        self.after(0, self._populate_all_users, all_users_list)

    def _populate_all_users(self, all_users_list):
        self.profile_updaters.clear()
        self.original_profiles.clear()
        for widget in self.all_users_frame.winfo_children(): widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhum usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        role_options = ["admin", "partner", "prefeitura", "telecom_user"]
        
        for user in all_users_list:
            email = user.get('email')
            self.original_profiles[email] = {'role': user.get('role'), 'company': user.get('company')}
            
            card = ctk.CTkFrame(self.all_users_frame)
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)
            
            info_text = f"{user.get('name', 'N/A')} (@{user.get('username', 'N/A')})"
            ctk.CTkLabel(card, text=info_text, anchor="w").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(card, text=email, anchor="w", text_color="gray60").grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")
            
            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="e")

            role_combo = ctk.CTkComboBox(controls_frame, values=role_options, width=150,
                                         command=partial(self._on_role_change, email))
            role_combo.set(user.get('role'))
            role_combo.pack(side="left", padx=(0, 10))

            company_combo = ctk.CTkComboBox(controls_frame, values=self.partner_companies, width=180)
            company_combo.set(user.get('company', ''))
            
            self.profile_updaters[email] = {'role_widget': role_combo, 'company_widget': company_combo}
            self._on_role_change(email, user.get('role'))

    def _on_role_change(self, email, selected_role):
        widgets = self.profile_updaters.get(email)
        if widgets:
            company_widget = widgets['company_widget']
            if selected_role == 'partner':
                company_widget.pack(side="left")
            else:
                company_widget.pack_forget()

    def save_profile_changes(self):
        changes_to_save = {}
        for email, widgets in self.profile_updaters.items():
            new_role = widgets['role_widget'].get()
            new_company = widgets['company_widget'].get() if new_role == 'partner' else ""
            
            original = self.original_profiles.get(email, {})
            if original.get('role') != new_role or original.get('company') != new_company:
                changes_to_save[email] = {'role': new_role, 'company': new_company}
        
        if not changes_to_save:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil de usuário foi alterado.")
            return
            
        for email, changes in changes_to_save.items():
            self.controller.update_user_profile(email, changes['role'], changes['company'])
        
        messagebox.showinfo("Sucesso", f"{len(changes_to_save)} perfis de usuário foram atualizados.")
        self.load_all_users()

    def setup_occurrences_tab(self):
        ctk.CTkLabel(self.occurrences_tab, text="Visão Geral de Todas as Ocorrências").pack(pady=5)
        self.all_occurrences_frame = ctk.CTkScrollableFrame(self.occurrences_tab, label_text="Carregando...")
        self.all_occurrences_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.occurrences_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        save_button = ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes)
        save_button.pack(side="left", padx=(0, 10), expand=True, fill="x")
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Lista", command=self.load_all_occurrences)
        refresh_button.pack(side="left", expand=True, fill="x")

    def load_all_occurrences(self):
        self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
        threading.Thread(target=self._load_occurrences_data_thread, daemon=True).start()

    def _load_occurrences_data_thread(self):
        all_occurrences_list = self.controller.get_all_occurrences()
        self.after(0, self._populate_all_occurrences, all_occurrences_list)

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

            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A')
            
            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            
            details_text = f"Registrado por: {item.get('Nome do Registrador', 'N/A')} (@{item.get('Username do Registrador', 'N/A')}) em {date}"
            ctk.CTkLabel(info_frame, text=details_text, anchor="w", text_color="gray60").pack(anchor="w")

            try:
                anexos = json.loads(item.get('Anexos', '[]'))
                if anexos:
                    ctk.CTkLabel(info_frame, text="(Contém Anexos)", text_color="cyan", font=ctk.CTkFont(slant="italic")).pack(anchor="w")
            except: pass
            
            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)

            status_combo = ctk.CTkComboBox(controls_frame, values=status_options, width=180)
            status_combo.set(self.original_statuses[item_id])
            status_combo.pack(side="left", padx=(0, 10))
            self.status_updaters[item_id] = status_combo

            open_button = ctk.CTkButton(controls_frame, text="Abrir", width=80, command=partial(self.controller.show_occurrence_details, item_id))
            open_button.pack(side="left")

    def save_status_changes(self):
        changes_to_save = {}
        for occ_id, combo_widget in self.status_updaters.items():
            if self.original_statuses.get(occ_id) != combo_widget.get():
                changes_to_save[occ_id] = combo_widget.get()
        self.controller.save_occurrence_status_changes(changes_to_save)
    
    def setup_access_tab(self):
        ctk.CTkLabel(self.access_tab, text="Solicitações de Acesso Pendentes").pack(pady=5)
        self.pending_users_frame = ctk.CTkScrollableFrame(self.access_tab, label_text="Carregando...")
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        refresh_button = ctk.CTkButton(self.access_tab, text="Atualizar Lista", command=self.load_access_requests)
        refresh_button.pack(pady=5, padx=5, fill="x")
    
    def setup_analysis_tab(self):
        pass

    def on_show(self):
        self.on_tab_change()

    def on_tab_change(self):
        selected_tab = self.tabview.get()
        if selected_tab == "Ocorrências": self.load_all_occurrences()
        elif selected_tab == "Gerenciar Acessos": self.load_access_requests()
        elif selected_tab == "Gerenciar Usuários": self.load_all_users()
        elif selected_tab == "Análise de Dados": pass

    def load_access_requests(self):
        self.pending_users_frame.configure(label_text="Carregando solicitações...")
        threading.Thread(target=self._load_access_data_thread, daemon=True).start()

    def _load_access_data_thread(self):
        pending_list = self.controller.get_pending_requests()
        self.after(0, self._populate_access_requests, pending_list)

    def _populate_access_requests(self, pending_list):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame)
            card.pack(fill="x", pady=5)
            company_info = f" ({user.get('company')})" if user.get('role') == 'partner' and user.get('company') else ""
            info_text = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\nE-mail: {user['email']}\nVínculo: {user['role']}{company_info}"
            ctk.CTkLabel(card, text=info_text, justify="left").pack(side="left", padx=10, pady=5)
            reject_button = ctk.CTkButton(card, text="Rejeitar", command=partial(self.controller.update_user_access, user['email'], 'rejected'), fg_color="red")
            reject_button.pack(side="right", padx=5, pady=5)
            approve_button = ctk.CTkButton(card, text="Aprovar", command=partial(self.controller.update_user_access, user['email'], 'approved'), fg_color="green")
            approve_button.pack(side="right", padx=5, pady=5)
