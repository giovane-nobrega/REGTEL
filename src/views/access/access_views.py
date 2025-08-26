# ==============================================================================
# ARQUIVO: src/views/access/access_views.py
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import re
import threading
import time

class RequestAccessView(ctk.CTkFrame):
    """ Tela para novos usuários solicitarem acesso ao sistema. """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=controller.BASE_COLOR)

        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)

        ctk.CTkLabel(center_frame, text="Solicitação de Acesso", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(center_frame, text="Seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.", wraplength=400, text_color="gray70").pack(pady=(0, 20))

        self.name_entry = ctk.CTkEntry(center_frame, placeholder_text="Nome Completo", width=300)
        self.name_entry.pack(pady=5)
        self.username_entry = ctk.CTkEntry(center_frame, placeholder_text="Nome de Usuário (ex: jsilva)", width=300)
        self.username_entry.pack(pady=5)
        self.role_combobox = ctk.CTkComboBox(center_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected)
        self.role_combobox.pack(pady=5)
        self.company_combobox = ctk.CTkComboBox(center_frame, values=[], width=300)
        self.subgroup_67_combobox = ctk.CTkComboBox(center_frame, values=["67_TELECOM_USER", "67_INTERNET_USER"], width=300)

        ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40).pack(pady=20, fill="x")
        ctk.CTkButton(center_frame, text="Sair", command=controller.perform_logout, height=40, fg_color="gray50", hover_color="gray40").pack(pady=10, fill="x")

        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")

    def _on_role_selected(self, selected_role):
        """ Controla a visibilidade dos campos dependentes. """
        self.company_combobox.pack_forget()
        self.subgroup_67_combobox.pack_forget()
        if selected_role == "Parceiro":
            self.company_combobox.configure(values=[c for c in self.partner_list if c != "67 INTERNET"])
            self.company_combobox.pack(pady=5)
        elif selected_role == "Prefeitura":
            self.company_combobox.configure(values=self.prefeitura_dept_list)
            self.company_combobox.pack(pady=5)
        elif selected_role == "Colaboradores 67":
            self.subgroup_67_combobox.pack(pady=5)

    def on_show(self):
        """ Limpa o formulário ao ser exibido. """
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")

    def submit(self):
        """ Envia os dados do formulário para o controlador. """
        full_name = self.name_entry.get()
        username = self.username_entry.get()
        main_group = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}.get(self.role_combobox.get())
        company_name = self.company_combobox.get() if main_group in ["PARTNER", "PREFEITURA"] else "TRR"
        sub_group = self.subgroup_67_combobox.get() if main_group == "67_TELECOM" else "USER"
        
        self.controller.submit_access_request(full_name, username, main_group, sub_group, company_name)

class PendingApprovalView(ctk.CTkFrame):
    """ Tela exibida enquanto o acesso do usuário está pendente de aprovação. """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=controller.BASE_COLOR)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)

        ctk.CTkLabel(center_frame, text="Acesso Pendente", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(center_frame, text="Sua solicitação está aguardando aprovação.", wraplength=450, text_color="gray70").pack(pady=(0, 20))
        self.status_label = ctk.CTkLabel(center_frame, text="Verificando o status...", font=ctk.CTkFont(size=14, slant="italic"), text_color=controller.ACCENT_COLOR)
        self.status_label.pack(pady=(0, 10))
        ctk.CTkButton(center_frame, text="Verificar Agora", command=self.check_status_now).pack(pady=(0, 10))
        ctk.CTkButton(center_frame, text="Sair", command=controller.perform_logout, height=40, fg_color="gray50", hover_color="gray40").pack(pady=10)

        self.is_running = False
        self.checker_thread = None

    def on_show(self):
        """ Inicia a verificação de status em segundo plano. """
        if not self.is_running:
            self.is_running = True
            self.checker_thread = threading.Thread(target=self._check_status_thread, daemon=True)
            self.checker_thread.start()

    def _check_status_thread(self):
        """ Thread que verifica o status do usuário periodicamente. """
        while self.is_running:
            user_profile = self.controller.user_service.get_user_status(self.controller.user_email)
            status = user_profile.get("status")

            if status == "approved":
                self.is_running = False
                self.controller.user_profile = user_profile
                self.controller.after(0, self.controller.navigate_based_on_status)
                break
            elif status == "rejected":
                self.is_running = False
                self.controller.after(0, lambda: messagebox.showerror("Acesso Negado", "Sua solicitação foi rejeitada."))
                self.controller.after(0, self.controller.perform_logout)
                break
            
            time.sleep(30)

    def check_status_now(self):
        """ Força uma verificação imediata do status. """
        if self.is_running:
            self.is_running = False
            if self.checker_thread and self.checker_thread.is_alive():
                self.checker_thread.join(timeout=1.5)
        self.on_show()
