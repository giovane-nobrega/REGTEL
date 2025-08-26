# ==============================================================================
# ARQUIVO: src/views/access_management_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de Gerenciamento de Acessos.
#            (VERSÃO CORRIGIDA PARA FUNCIONALIDADE E LAYOUT)
# ==============================================================================

import customtkinter as ctk
from functools import partial
import threading
from tkinter import messagebox
from builtins import super, list, Exception, print, str, hasattr, len

class AccessManagementView(ctk.CTkFrame):
    """
    Tela para administradores gerenciarem solicitações de acesso pendentes.
    Permite aprovar ou rejeitar novos usuários.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Gerenciar Solicitações de Acesso",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.pending_users_frame = ctk.CTkScrollableFrame(self, label_text="Carregando solicitações...",
                                                          fg_color="gray10",
                                                          label_text_color=self.controller.TEXT_COLOR)
        self.pending_users_frame.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        ctk.CTkButton(self, text="Atualizar Lista", command=self.load_access_requests,
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=2, column=0, pady=(0, 10), padx=20, sticky="ew")
        
        ctk.CTkButton(self, text="Voltar ao Dashboard", command=lambda: self.controller.show_frame("AdminDashboardView"),
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=3, column=0, pady=(0, 10), padx=20, sticky="ew")

    def on_show(self):
        """
        Chamado sempre que esta tela é exibida.
        Carrega as solicitações de acesso.
        """
        print("DEBUG: AccessManagementView exibida. Carregando solicitações de acesso.")
        self.pending_users_frame.configure(label_text="Carregando solicitações...")
        self.update_idletasks()
        self.controller.get_all_users(force_refresh=True) 
        self.load_access_requests()

    def load_access_requests(self):
        """
        Inicia o carregamento das solicitações de acesso pendentes em uma thread separada.
        """
        threading.Thread(target=self._load_access_requests_thread, daemon=True).start()

    def _load_access_requests_thread(self):
        """
        Busca as solicitações de acesso pendentes e as popula na UI.
        """
        pending_list = self.controller.get_pending_requests()
        print(f"DEBUG: Solicitações pendentes obtidas: {pending_list}")
        self.after(0, self._populate_access_requests, pending_list)


    def _populate_access_requests(self, pending_list):
        """
        Popula o frame rolável com os cards das solicitações de acesso pendentes.
        :param pending_list: Lista de dicionários com as solicitações pendentes.
        """
        for widget in self.pending_users_frame.winfo_children():
            widget.destroy()

        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")

        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5, padx=5)

            company_info = f" ({user.get('company')})" if user.get('company') else ""
            info_text = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\n" \
                        f"E-mail: {user['email']}\nVínculo: {user['main_group']}{company_info}"

            ctk.CTkLabel(card, text=info_text, justify="left",
                         text_color=self.controller.TEXT_COLOR).pack(side="left", padx=10, pady=5)

            ctk.CTkButton(card, text="Rejeitar",
                          command=partial(self._handle_access_update, user['email'], 'rejected'),
                          fg_color=self.controller.DANGER_COLOR, text_color=self.controller.TEXT_COLOR,
                          hover_color=self.controller.DANGER_HOVER_COLOR,
                          width=80, height=30).pack(side="right", padx=5, pady=5)

            ctk.CTkButton(card, text="Aprovar",
                          command=partial(self._handle_access_update, user['email'], 'approved'),
                          fg_color="green",
                          text_color=self.controller.TEXT_COLOR,
                          hover_color="darkgreen",
                          width=80, height=30).pack(side="right", padx=5, pady=5)

    def _handle_access_update(self, email, new_status):
        """
        Lida com a atualização do status de acesso de um usuário.
        :param email: E-mail do usuário a ser atualizado.
        :param new_status: O novo status ('approved' ou 'rejected').
        """
        self.controller.update_user_access(email, new_status)
