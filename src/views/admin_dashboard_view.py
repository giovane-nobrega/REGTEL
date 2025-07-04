import customtkinter as ctk
from functools import partial
class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_statuses = {}
        self.status_updaters = {}
        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 10))
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.access_tab = tabview.add("Gerir Acessos")
        self.occurrences_tab = tabview.add("Ocorrências")
        self.setup_access_tab()
        self.setup_occurrences_tab()
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.pack(pady=10, padx=20, fill="x")
    def setup_access_tab(self):
        ctk.CTkLabel(self.access_tab, text="Solicitações de Acesso Pendentes").pack()
        self.pending_users_frame = ctk.CTkScrollableFrame(self.access_tab, label_text="A carregar solicitações...")
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        refresh_button = ctk.CTkButton(self.access_tab, text="Atualizar Lista", command=self.load_access_requests)
        refresh_button.pack(pady=5)
    def setup_occurrences_tab(self):
        ctk.CTkLabel(self.occurrences_tab, text="Visão Geral de Todas as Ocorrências").pack()
        self.all_occurrences_frame = ctk.CTkScrollableFrame(self.occurrences_tab, label_text="A carregar ocorrências...")
        self.all_occurrences_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.occurrences_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5)
        save_button = ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes)
        save_button.pack(side="left", padx=(0, 10))
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Lista", command=self.load_all_occurrences)
        refresh_button.pack(side="left")
    def on_show(self):
        self.load_access_requests()
        self.load_all_occurrences()
    def load_access_requests(self):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        pending_list = self.controller.get_pending_requests()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame)
            card.pack(fill="x", pady=5)
            info_text = f"E-mail: {user['email']}\nVínculo Solicitado: {user['role']}"
            ctk.CTkLabel(card, text=info_text, justify="left").pack(side="left", padx=10, pady=5)
            reject_button = ctk.CTkButton(card, text="Rejeitar", command=partial(self.controller.update_user_access, user['email'], 'rejected'), fg_color="red")
            reject_button.pack(side="right", padx=5, pady=5)
            approve_button = ctk.CTkButton(card, text="Aprovar", command=partial(self.controller.update_user_access, user['email'], 'approved'), fg_color="green")
            approve_button.pack(side="right", padx=5, pady=5)
    def load_all_occurrences(self):
        self.status_updaters.clear()
        self.original_statuses.clear()
        for widget in self.all_occurrences_frame.winfo_children(): widget.destroy()
        all_occurrences_list = self.controller.get_all_occurrences()
        if not all_occurrences_list:
            self.all_occurrences_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
        self.all_occurrences_frame.configure(label_text="")
        status_options = ["Registrado", "Em Análise", "Aguardando Terceiros", "Resolvido", "Cancelado"]
        for item in all_occurrences_list:
            item_id = item.get('ID', 'N/A')
            self.original_statuses[item_id] = item.get('Status', 'N/A')
            card = ctk.CTkFrame(self.all_occurrences_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1); card.grid_columnconfigure(1, weight=0)
            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A'); email = item.get('Email do Registrador', 'N/A')
            ctk.CTkLabel(card, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
            ctk.CTkLabel(card, text=f"Registado por: {email} em {date}", anchor="w", text_color="gray60").grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
            status_combo = ctk.CTkComboBox(card, values=status_options, width=180)
            status_combo.set(self.original_statuses[item_id])
            status_combo.grid(row=1, column=1, sticky="e", padx=10, pady=(0,5))
            self.status_updaters[item_id] = status_combo
    def save_status_changes(self):
        changes_to_save = {}
        for occ_id, combo_widget in self.status_updaters.items():
            if self.original_statuses.get(occ_id) != combo_widget.get():
                changes_to_save[occ_id] = combo_widget.get()
        self.controller.save_occurrence_status_changes(changes_to_save)