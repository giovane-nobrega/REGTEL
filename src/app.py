# ==============================================================================
# FICHEIRO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação. (VERSÃO COM CORREÇÃO DE NAVEGAÇÃO E ENCERRAMENTO)
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import threading
import os
import sys
import requests
import subprocess
import time
from builtins import super, print, Exception, hasattr, len, max, range, int, str, dict, open

# Importações dos módulos de serviço e das views
from services.auth_service import AuthService
from services.sheets_service import SheetsService
from views.access_views import RequestAccessView, PendingApprovalView
from views.equipment_view import EquipmentView
from views.history_view import HistoryView
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.occurrence_detail_view import OccurrenceDetailView
from views.registration_view import RegistrationView
from views.simple_call_view import SimpleCallView
from views.notification_popup import NotificationPopup

# NOVAS IMPORTAÇÕES PARA AS VIEWS DE GERENCIAMENTO
from views.admin_dashboard_view import AdminDashboardView
from views.access_management_view import AccessManagementView
from views.user_management_view import UserManagementView


class App(ctk.CTk):
    def __init__(self):
        # --- Configuração do Logging ---
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "REGTEL_Logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file_path = os.path.join(log_dir, "app_debug.log")
        self._log_file = None

        try:
            self._log_file = open(self.log_file_path, 'w', encoding='utf-8')
            sys.stdout = self._log_file
            sys.stderr = self._log_file
            print(f"--- REGTEL Debug Log Iniciado em: {self.log_file_path} ---")
        except Exception as e:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            messagebox.showerror("Erro de Log", f"Não foi possível iniciar o log da aplicação: {e}")

        super().__init__()
        self.title("Plataforma de Registro de Ocorrências (REGTEL)")
        self.geometry("900x750")
        self.minsize(800, 650)

        # --- Lidar com o encerramento da janela ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Configurações de Aparência ---
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

        # --- Ícone da Janela ---
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        icon_path = os.path.join(base_path, 'icon.ico')
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone da janela: {e}")

        # --- Inicialização de Serviços e Variáveis ---
        self.auth_service = AuthService()
        self.sheets_service = SheetsService(self.auth_service)
        self.credentials = None
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.detail_window = None
        self.occurrences_cache = None
        self.users_cache = None
        self.current_frame = None

        # --- Configuração do Layout Principal ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        container = ctk.CTkFrame(self, fg_color=self.BASE_COLOR)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- Inicialização das Telas (Views) ---
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
            frame.grid(row=0, column=0, sticky="nsew")

        self.check_initial_login()

    def on_closing(self):
        """Função chamada quando a janela principal é fechada."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if self._log_file:
            self._log_file.close()
        self.destroy()

    def show_frame(self, page_name):
        """Mostra uma tela específica da aplicação."""
        frame = self.frames[page_name]
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()
        self.current_frame = page_name

    def check_initial_login(self):
        """Verifica se já existem credenciais salvas."""
        self.frames["LoginView"].set_loading_state("Verificando credenciais...")
        threading.Thread(target=self._check_initial_login_thread, daemon=True).start()

    def _check_initial_login_thread(self):
        creds = self.auth_service.load_user_credentials()
        if creds:
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: self.show_frame("LoginView"))
            self.after(0, self.frames["LoginView"].set_default_state)

    def perform_login(self):
        """Inicia o fluxo de login do Google."""
        self.frames["LoginView"].set_loading_state("Aguardando autenticação no navegador...")
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
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        """Busca o perfil do usuário após o login."""
        self.user_email = str(self.auth_service.get_user_email(self.credentials))
        if "Erro" in self.user_email or not self.user_email.strip():
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail."))
            self.after(0, self.perform_logout)
            return
        self.user_profile = self.sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        """Navega para a tela correta com base no status do usuário."""
        status = self.user_profile.get("status")
        main_group = self.user_profile.get("main_group")
        sub_group = self.user_profile.get("sub_group")

        if status == "approved":
            # CORREÇÃO: Garante que ADMIN e SUPER_ADMIN vão para o Dashboard
            if main_group == "67_TELECOM" and sub_group in ["ADMIN", "SUPER_ADMIN"]:
                self.show_frame("AdminDashboardView")
            else:
                self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            self.show_frame("RequestAccessView")

    def get_all_users(self, force_refresh=False):
        """Obtém todos os usuários, usando cache se possível."""
        if force_refresh or self.users_cache is None:
            self.users_cache = self.sheets_service.get_all_users()
        return self.users_cache

    def perform_logout(self):
        """Realiza o logout do usuário."""
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.users_cache = None
        self.occurrences_cache = None
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()
