# ==============================================================================
# ARQUIVO: src/views/management/access_management_view.py
# ==============================================================================

import customtkinter as ctk
import threading
from functools import partial

class AccessManagementView(ctk.CTkFrame):
    """ Tela para gerenciar solicitações de acesso pendentes. """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=controller.BASE_COLOR)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Gerenciar Solicitações de Acesso", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.pending_users_frame = ctk.CTkScrollableFrame(self, label_text="Carregando solicitações...")
        self.pending_users_frame.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        ctk.CTkButton(self, text="Atualizar Lista", command=self.load_access_requests).grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        ctk.CTkButton(self, text="Voltar ao Dashboard", command=lambda: controller.show_frame("AdminDashboardView")).grid(row=3, column=0, pady=10, padx=20, sticky="ew")

    def on_show(self):
        self.load_access_requests()

    def load_access_requests(self):
        """ Carrega as solicitações de acesso em segundo plano. """
        self.pending_users_frame.configure(label_text="Carregando...")
        for widget in self.pending_users_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_requests_thread, daemon=True).start()

    def _load_requests_thread(self):
        pending_list = self.controller.get_pending_requests()
        self.after(0, self._populate_requests, pending_list)

    def _populate_requests(self, pending_list):
        """ Popula a UI com as solicitações pendentes. """
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5, padx=5)
            info = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\nE-mail: {user.get('email')}"
            ctk.CTkLabel(card, text=info, justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(card, text="Rejeitar", command=partial(self.controller.update_user_access, user['email'], 'rejected'), fg_color="red").pack(side="right", padx=5, pady=5)
            ctk.CTkButton(card, text="Aprovar", command=partial(self.controller.update_user_access, user['email'], 'approved'), fg_color="green").pack(side="right", padx=5, pady=5)