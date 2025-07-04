import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading


class AdminDashboardView(ctk.CTkFrame):
    """Tela do dashboard de gestão para administradores."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_statuses = {}
        self.status_updaters = {}
        self.original_roles = {}
        self.role_updaters = {}

        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(
            size=24, weight="bold")).pack(pady=(10, 10))

        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Ordem das abas alterada
        self.occurrences_tab = self.tabview.add("Ocorrências")
        self.access_tab = self.tabview.add("Gerir Acessos")
        self.users_tab = self.tabview.add("Gerir Utilizadores")

        self.setup_occurrences_tab()
        self.setup_access_tab()
        self.setup_users_tab()

        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.pack(pady=10, padx=20, fill="x")

    def setup_access_tab(self):
        """Configura os widgets da aba de gestão de acessos."""
        ctk.CTkLabel(self.access_tab,
                     text="Solicitações de Acesso Pendentes").pack()
        self.pending_users_frame = ctk.CTkScrollableFrame(
            self.access_tab, label_text="A carregar...")
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        refresh_button = ctk.CTkButton(
            self.access_tab, text="Atualizar Lista", command=self.load_access_requests)
        refresh_button.pack(pady=5)

    def setup_users_tab(self):
        """Configura os widgets da aba de gestão de utilizadores."""
        ctk.CTkLabel(self.users_tab,
                     text="Lista de Todos os Utilizadores").pack()
        self.all_users_frame = ctk.CTkScrollableFrame(
            self.users_tab, label_text="A carregar...")
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.users_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5)
        save_button = ctk.CTkButton(
            button_frame, text="Salvar Alterações de Perfil", command=self.save_role_changes)
        save_button.pack(side="left", padx=(0, 10))
        refresh_button = ctk.CTkButton(
            button_frame, text="Atualizar Lista", command=self.load_all_users)
        refresh_button.pack(side="left")

    def setup_occurrences_tab(self):
        """Configura os widgets da aba de visualização de ocorrências."""
        ctk.CTkLabel(self.occurrences_tab,
                     text="Visão Geral de Todas as Ocorrências").pack()
        self.all_occurrences_frame = ctk.CTkScrollableFrame(
            self.occurrences_tab, label_text="A carregar...")
        self.all_occurrences_frame.pack(
            fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(
            self.occurrences_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5)
        save_button = ctk.CTkButton(
            button_frame, text="Salvar Alterações de Status", command=self.save_status_changes)
        save_button.pack(side="left", padx=(0, 10))
        refresh_button = ctk.CTkButton(
            button_frame, text="Atualizar Lista", command=self.load_all_occurrences)
        refresh_button.pack(side="left")

    def on_show(self):
        """Método chamado pelo controlador sempre que esta tela é exibida."""
        self.on_tab_change()

    def on_tab_change(self):
        """Carrega os dados da aba atualmente selecionada."""
        selected_tab = self.tabview.get()
        if selected_tab == "Ocorrências":
            self.load_all_occurrences()
        elif selected_tab == "Gerir Acessos":
            self.load_access_requests()
        elif selected_tab == "Gerir Utilizadores":
            self.load_all_users()

    def load_access_requests(self):
        """Inicia o carregamento dos pedidos de acesso em segundo plano."""
        self.pending_users_frame.configure(
            label_text="A carregar solicitações...")
        threading.Thread(target=self._load_access_data_thread,
                         daemon=True).start()

    def _load_access_data_thread(self):
        """Busca os dados e agenda a atualização da UI."""
        pending_list = self.controller.get_pending_requests()
        self.after(0, self._populate_access_requests, pending_list)

    def _populate_access_requests(self, pending_list):
        """Preenche a UI com os pedidos de acesso."""
        for widget in self.pending_users_frame.winfo_children():
            widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(
                label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame)
            card.pack(fill="x", pady=5)
            info_text = f"Nome: {user.get('name', 'N/A')} ({user.get('username', 'N/A')})\nE-mail: {user['email']}\nVínculo: {user['role']}"
            ctk.CTkLabel(card, text=info_text, justify="left").pack(
                side="left", padx=10, pady=5)
            reject_button = ctk.CTkButton(card, text="Rejeitar", command=partial(
                self.controller.update_user_access, user['email'], 'rejected'), fg_color="red")
            reject_button.pack(side="right", padx=5, pady=5)
            approve_button = ctk.CTkButton(card, text="Aprovar", command=partial(
                self.controller.update_user_access, user['email'], 'approved'), fg_color="green")
            approve_button.pack(side="right", padx=5, pady=5)

    def load_all_users(self):
        """Inicia o carregamento de todos os utilizadores em segundo plano."""
        self.all_users_frame.configure(label_text="A carregar utilizadores...")
        threading.Thread(target=self._load_users_data_thread,
                         daemon=True).start()

    def _load_users_data_thread(self):
        """Busca os dados e agenda a atualização da UI."""
        all_users_list = self.controller.get_all_users()
        self.after(0, self._populate_all_users, all_users_list)

    def _populate_all_users(self, all_users_list):
        """Preenche a UI com todos os utilizadores."""
        self.role_updaters.clear()
        self.original_roles.clear()
        for widget in self.all_users_frame.winfo_children():
            widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(
                label_text="Nenhum utilizador encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        role_options = ["admin", "partner", "prefeitura"]
        for user in all_users_list:
            email = user.get('email')
            self.original_roles[email] = user.get('role')
            card = ctk.CTkFrame(self.all_users_frame)
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)
            info_text = f"{user.get('name', 'Nome não informado')} (@{user.get('username', 'N/A')})"
            info_label = ctk.CTkLabel(card, text=info_text, anchor="w")
            info_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            role_combo = ctk.CTkComboBox(card, values=role_options, width=150)
            role_combo.set(user.get('role'))
            role_combo.grid(row=0, column=1, padx=10, pady=10, sticky="e")
            self.role_updaters[email] = role_combo

    def save_role_changes(self):
        """Verifica e salva as alterações de perfil dos utilizadores."""
        changes_to_save = {}
        for email, combo_widget in self.role_updaters.items():
            new_role = combo_widget.get()
            if self.original_roles.get(email) != new_role:
                changes_to_save[email] = new_role
        if not changes_to_save:
            messagebox.showinfo("Nenhuma Alteração",
                                "Nenhum perfil de utilizador foi alterado.")
            return
        for email, new_role in changes_to_save.items():
            self.controller.update_user_role(email, new_role)

    def load_all_occurrences(self):
        """Inicia o carregamento de todas as ocorrências em segundo plano."""
        self.all_occurrences_frame.configure(
            label_text="A carregar ocorrências...")
        threading.Thread(
            target=self._load_occurrences_data_thread, daemon=True).start()

    def _load_occurrences_data_thread(self):
        """Busca os dados e agenda a atualização da UI."""
        all_occurrences_list = self.controller.get_all_occurrences()
        self.after(0, self._populate_all_occurrences, all_occurrences_list)

    def _populate_all_occurrences(self, all_occurrences_list):
        """Preenche a UI com todas as ocorrências."""
        self.status_updaters.clear()
        self.original_statuses.clear()
        for widget in self.all_occurrences_frame.winfo_children():
            widget.destroy()
        if not all_occurrences_list:
            self.all_occurrences_frame.configure(
                label_text="Nenhuma ocorrência encontrada.")
            return
        self.all_occurrences_frame.configure(label_text="")
        status_options = ["Registrado", "Em Análise",
                          "Aguardando Terceiros", "Resolvido", "Cancelado"]
        for item in all_occurrences_list:
            item_id = item.get('ID', 'N/A')
            self.original_statuses[item_id] = item.get('Status', 'N/A')
            card = ctk.CTkFrame(self.all_occurrences_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=0)
            title = item.get('Título da Ocorrência',
                             item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A')
            email = item.get('Email do Registrador', 'N/A')
            ctk.CTkLabel(card, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"),
                         anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
            ctk.CTkLabel(card, text=f"Registado por: {email} em {date}", anchor="w", text_color="gray60").grid(
                row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            status_combo = ctk.CTkComboBox(
                card, values=status_options, width=180)
            status_combo.set(self.original_statuses[item_id])
            status_combo.grid(row=1, column=1, sticky="e",
                              padx=10, pady=(0, 5))
            self.status_updaters[item_id] = status_combo

    def save_status_changes(self):
        """Verifica quais status foram alterados e envia para o controlador."""
        changes_to_save = {}
        for occ_id, combo_widget in self.status_updaters.items():
            if self.original_statuses.get(occ_id) != combo_widget.get():
                changes_to_save[occ_id] = combo_widget.get()
        self.controller.save_occurrence_status_changes(changes_to_save)
