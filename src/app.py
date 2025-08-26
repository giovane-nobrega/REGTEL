# ==============================================================================
# ARQUIVO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação. (VERSÃO REATORADA)
#            Agora delega a lógica de negócio para os serviços específicos
#            (OccurrenceService, UserService, AuthService).
# ==============================================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import requests
import subprocess
from builtins import super, print, Exception, hasattr, len, max, range, int, str, dict, open

# Importações dos módulos de serviço e das views
from services.auth_service import AuthService
from services.sheets_service import SheetsService
from services.occurrence_service import OccurrenceService # NOVO
from services.user_service import UserService # NOVO

from views.access_views import RequestAccessView, PendingApprovalView
from views.admin_dashboard_view import AdminDashboardView
from views.equipment_view import EquipmentView
from views.history_view import HistoryView
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.occurrence_detail_view import OccurrenceDetailView
from views.registration_view import RegistrationView
from views.simple_call_view import SimpleCallView
from views.notification_popup import NotificationPopup
from views.access_management_view import AccessManagementView
from views.user_management_view import UserManagementView


class App(ctk.CTk):
    """
    Classe principal da aplicação. Atua como o controlador central (Controller),
    gerenciando a navegação entre as telas (Views) e a comunicação com os
    serviços de backend (Services).
    """
    def __init__(self):
        super().__init__()
        # ... (configurações iniciais da janela, cores, ícone, etc. - sem alterações)
        self.title("Plataforma de Registro de Ocorrências (REGTEL)")
        self.geometry("900x750")
        self.minsize(800, 650)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.PRIMARY_COLOR = "#00BFFF"
        self.ACCENT_COLOR = "#00CED1"
        self.BASE_COLOR = "#0A0E1A"
        self.TEXT_COLOR = "#FFFFFF"
        self.DANGER_COLOR = "#D32F2F"
        self.DANGER_HOVER_COLOR = "#B71C1C"
        self.GRAY_BUTTON_COLOR = "gray50"
        self.GRAY_HOVER_COLOR = "gray40"
        self.configure(fg_color=self.BASE_COLOR)
        # ... (fim das configurações iniciais)

        # --- Injeção de Dependência dos Serviços ---
        self.auth_service = AuthService()
        self.sheets_service = SheetsService(self.auth_service)
        self.user_service = UserService(self.sheets_service) # NOVO
        self.occurrence_service = OccurrenceService(self.sheets_service, self.auth_service) # NOVO

        # --- Estado da Aplicação ---
        self.credentials = None
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.detail_window = None
        self.testes_adicionados = []
        self.editing_index = None
        
        # --- Configuração das Views ---
        container = ctk.CTkFrame(self, fg_color=self.BASE_COLOR)
        container.pack(fill="both", expand=True)
        self.frames = {}
        view_classes = (
            LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
            AdminDashboardView, HistoryView, RegistrationView, SimpleCallView,
            EquipmentView, AccessManagementView, UserManagementView
        )
        for F in view_classes:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        self.current_frame = None
        self.previous_frame_name = None

        self.check_initial_login()
        # ... (configurações de atualização - sem alterações)

    # ==============================================================================
    # --- MÉTODOS DE NAVEGAÇÃO E CONTROLE DE TELA ---
    # ==============================================================================
    def show_frame(self, page_name, from_view=None, mode="all"):
        # ... (lógica de show_frame - sem alterações)
        if from_view and self.current_frame and from_view != page_name:
            self.previous_frame_name = from_view
        elif not from_view:
            self.previous_frame_name = None

        frame = self.frames[page_name]
        if hasattr(frame, 'on_show'):
            if page_name == "HistoryView":
                frame.on_show(self.previous_frame_name, mode=mode)
            else:
                frame.on_show()
        frame.tkraise()
        self.current_frame = page_name

    def show_occurrence_details(self, occurrence_id):
        if self.detail_window and self.detail_window.winfo_exists():
            self.detail_window.focus()
            return
        # DELEGAÇÃO: Chama o serviço de ocorrências
        occurrence_data = self.occurrence_service.get_occurrence_details(occurrence_id)
        if occurrence_data:
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

    # ==============================================================================
    # --- FLUXO DE AUTENTICAÇÃO E PERFIL DE USUÁRIO ---
    # ==============================================================================
    def check_initial_login(self):
        self.frames["LoginView"].set_loading_state("Verificando credenciais...")
        threading.Thread(target=self._check_initial_login_thread, daemon=True).start()

    def _check_initial_login_thread(self):
        creds = self.auth_service.load_user_credentials()
        if creds:
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, self.frames["LoginView"].set_default_state)
            self.after(0, self.show_frame, "LoginView")

    def perform_login(self):
        self.frames["LoginView"].set_loading_state("Aguarde... Uma janela do navegador foi aberta...")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = self.auth_service.run_login_flow()
        if creds:
            self.credentials = creds
            self.after(0, self.deiconify)
            self.after(0, self.lift)
            self.after(0, self.focus_force)
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login falhou."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        self.user_email = str(self.auth_service.get_user_email(self.credentials))
        if "Erro" in self.user_email or not self.user_email.strip():
            messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail.")
            self.perform_logout()
            return
        # DELEGAÇÃO: Chama o serviço de usuário
        self.user_profile = self.user_service.get_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        # ... (lógica de navegação baseada no status - sem alterações)
        status = self.user_profile.get("status")
        if status == "approved":
            main_menu = self.frames["MainMenuView"]
            main_menu.update_user_info(self.user_email, self.user_profile, "1.0.2") # Exemplo de versão
            if self.user_profile.get("main_group") == "67_TELECOM" and self.user_profile.get("sub_group") == "SUPER_ADMIN":
                self.show_frame("AdminDashboardView")
            else:
                self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            self.show_frame("RequestAccessView")

    def perform_logout(self):
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    # ==============================================================================
    # --- MÉTODOS DELEGADOS AO USER SERVICE ---
    # ==============================================================================
    def submit_access_request(self, full_name, username, main_group, sub_group, company_name=None):
        if not self.user_email or "Erro" in self.user_email:
            messagebox.showerror("Erro Crítico", "Não foi possível obter seu e-mail. Tente fazer login novamente.")
            self.perform_logout()
            return
        # DELEGAÇÃO:
        success, message = self.user_service.submit_access_request(self.user_email, full_name, username, main_group, sub_group, company_name)
        if success:
            NotificationPopup(self, message="Solicitação enviada com sucesso!", type="success")
            self.show_frame("PendingApprovalView")
        else:
            messagebox.showerror("Erro ao Enviar Solicitação", message)

    def get_all_users(self, force_refresh=False):
        # DELEGAÇÃO:
        return self.user_service.get_all_users(force_refresh)

    def get_pending_requests(self):
        # DELEGAÇÃO:
        return self.user_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        # DELEGAÇÃO:
        success, message = self.user_service.update_user_access(email, new_status)
        if success:
            NotificationPopup(self, message=f"Acesso para {email} foi atualizado.", type="success")
            self.frames["AccessManagementView"].load_access_requests()
        else:
            messagebox.showerror("Erro", message)

    def update_user_profile(self, changes: dict):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")
            return
        # DELEGAÇÃO:
        success, message = self.user_service.update_user_profiles_batch(changes)
        if success:
            NotificationPopup(self, message=f"{len(changes)} perfil(is) atualizados.", type="success")
            self.frames["UserManagementView"].load_all_users(force_refresh=True)
        else:
            messagebox.showerror("Erro ao Salvar", message)

    def get_current_user_profile(self):
        # DELEGAÇÃO:
        return self.user_service.get_user_status(self.user_email)

    # ==============================================================================
    # --- MÉTODOS DELEGADOS AO OCCURRENCE SERVICE ---
    # ==============================================================================
    def get_all_occurrences(self, force_refresh=False):
        # DELEGAÇÃO:
        return self.occurrence_service.get_all_occurrences_for_user(self.user_email, force_refresh)

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        # DELEGAÇÃO:
        success, message = self.occurrence_service.save_batch_status_changes(changes)
        if success:
            NotificationPopup(self, message=f"Status de {len(changes)} ocorrência(s) salvos.", type="success")
            # Recarrega as views relevantes
            if "AdminDashboardView" in self.frames and hasattr(self.frames["AdminDashboardView"], '_occurrences_tab_initialized'):
                self.frames["AdminDashboardView"].load_all_occurrences(force_refresh=True)
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
        else:
            messagebox.showerror("Erro", message)

    def update_occurrence_status_from_history(self, occurrence_id, new_status):
        # DELEGAÇÃO:
        success, message = self.occurrence_service.update_status_from_history(occurrence_id, new_status)
        if success:
            NotificationPopup(self, message=f"Status da ocorrência {occurrence_id} atualizado.", type="success")
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
        else:
            messagebox.showerror("Erro", message)

    def submit_simple_call_occurrence(self, form_data):
        view = self.frames["SimpleCallView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_occurrence_thread, args=("SimpleCallView", self.occurrence_service.submit_simple_call, self.user_email, form_data), daemon=True).start()

    def submit_equipment_occurrence(self, data, attachment_paths=None):
        view = self.frames["EquipmentView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_occurrence_thread, args=("EquipmentView", self.occurrence_service.submit_equipment_occurrence, self.credentials, self.user_email, data, attachment_paths), daemon=True).start()

    def submit_full_occurrence(self, title):
        # ... (lógica de validação do formulário - sem alterações)
        view = self.frames["RegistrationView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_occurrence_thread, args=("RegistrationView", self.occurrence_service.submit_full_occurrence, self.user_email, title, self.testes_adicionados.copy()), daemon=True).start()

    def _submit_occurrence_thread(self, view_name, service_method, *args):
        """
        Thread genérica para submissão de ocorrências.
        """
        success, message = service_method(*args)
        self.after(0, self._on_submission_finished, view_name, success, message)

    def _on_submission_finished(self, view_name, success, message):
        """
        Callback executado na thread principal após a submissão de uma ocorrência.
        """
        view = self.frames[view_name]
        if hasattr(view, 'set_submitting_state'):
            view.set_submitting_state(False)

        if success:
            NotificationPopup(self, message=message, type="success")
            if hasattr(view, 'on_show'):
                 view.on_show()
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Ocorreu um Erro", f"Não foi possível completar a operação: {message}")
