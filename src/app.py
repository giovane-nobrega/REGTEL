# ==============================================================================
# FICHEIRO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação.
# DATA DA ATUALIZAÇÃO: 28/08/2025
# ==============================================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import requests
import subprocess
import time
from services.auth_service import AuthService
from services.sheets_service import SheetsService as SheetsServiceClass
from services.occurrence_service import OccurrenceService
from services.user_service import UserService

# --- ATUALIZAÇÃO: Imports das views ajustados para a nova estrutura de pastas ---
from views.access.access_views import RequestAccessView, PendingApprovalView
from views.management.admin_dashboard_view import AdminDashboardView
from views.registration.equipment_view import EquipmentView
from views.main.history_view import HistoryView
from views.main.login_view import LoginView
from views.main.main_menu_view import MainMenuView
from views.main.occurrence_detail_view import OccurrenceDetailView
from views.registration.registration_view import RegistrationView
from views.registration.simple_call_view import SimpleCallView
from views.components.notification_popup import NotificationPopup
from views.management.access_management_view import AccessManagementView
from views.management.user_management_view import UserManagementView


class App(ctk.CTk):
    """
    Controlador principal que gere a janela, a navegação entre frames (telas)
    e a comunicação com os serviços de back-end.
    """
    # --- CONSTANTES DE CONFIGURAÇÃO ---
    VERSION = "3.1.0"
    VERSION_URL = "https://raw.githubusercontent.com/Valente97/regtel/main/version.json"
    NEW_INSTALLER_DOWNLOAD_URL = ""

    # --- ESQUEMA DE CORES ---
    BASE_COLOR = "#0A0E1A"
    PRIMARY_COLOR = "#1C274C"
    ACCENT_COLOR = "#3A7EBF"
    TEXT_COLOR = "#FFFFFF"
    DANGER_COLOR = "#BF3A3A"
    DANGER_HOVER_COLOR = "#A93232"
    GRAY_BUTTON_COLOR = "#333333"
    GRAY_HOVER_COLOR = "#444444"

    def __init__(self, *args, **kwargs):
        """
        Inicializa a aplicação, configura a janela principal,
        instancia os serviços e prepara os frames (telas).
        """
        super().__init__(*args, **kwargs)

        self.title(f"REGTEL - Plataforma de Ocorrências v{self.VERSION}")
        self.geometry("800x600")
        self.minsize(600, 500)

        # Configura o layout da janela principal para que os frames se expandam
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- INICIALIZAÇÃO DOS SERVIÇOS ---
        self.auth_service = AuthService()
        self.sheets_service = SheetsServiceClass(self.auth_service)
        self.occurrence_service = OccurrenceService(self.sheets_service, self.auth_service)
        self.user_service = UserService(self.sheets_service)

        # Variáveis de estado do utilizador
        self.user_email = ""
        self.user_profile = {}
        self.frames = {}
        self._current_frame_name = None

        # Cria e armazena todas as telas da aplicação
        # Nota: OccurrenceDetailView é um Toplevel, não um frame principal
        for F in (LoginView, MainMenuView, RegistrationView, HistoryView,
                  RequestAccessView, PendingApprovalView, SimpleCallView,
                  EquipmentView, AdminDashboardView, AccessManagementView,
                  UserManagementView):
            frame_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Exibe a tela de login inicial
        self.show_frame("LoginView")

    def show_frame(self, frame_name, from_view=None, **kwargs):
        """
        Mostra um frame específico e, se o frame tiver um método `on_show`,
        chama-o para atualizar os seus dados.
        """
        if self._current_frame_name:
             self.frames[self._current_frame_name].previous_view = from_view

        frame = self.frames[frame_name]
        if hasattr(frame, 'on_show'):
            frame.on_show(**kwargs)
        frame.tkraise()
        self._current_frame_name = frame_name


    def perform_login(self):
        """
        Inicia o processo de login em uma thread separada para não bloquear a UI.
        """
        login_view = self.frames["LoginView"]
        login_view.set_loading_state("A autenticar com o Google...")
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        """
        Thread que executa o fluxo de autenticação.
        """
        credentials = self.auth_service.load_user_credentials()
        
        # Se não há credenciais válidas, inicia o fluxo de login OAuth
        if not credentials:
            credentials = self.auth_service.run_login_flow()
        
        self.after(0, self._handle_login_result, credentials)

    def _handle_login_result(self, credentials):
        """
        Processa o resultado do login na thread principal da UI.
        """
        login_view = self.frames["LoginView"]
        if credentials:
            self.user_email = self.auth_service.get_user_email(credentials)
            self._post_login_flow()
        else:
            login_view.set_default_state()
            messagebox.showerror("Login Falhou", "Não foi possível autenticar com o Google.")

    def _post_login_flow(self):
        """
        Após um login bem-sucedido, busca o perfil do utilizador e navega para a tela apropriada.
        """
        login_view = self.frames["LoginView"]
        login_view.set_loading_state("A verificar o seu perfil de utilizador...")

        self.user_profile = self.user_service.get_user_status(self.user_email)

        # Inicia a verificação de atualização em segundo plano
        threading.Thread(target=self.check_for_updates, daemon=True).start()

        self.navigate_based_on_status()

    def navigate_based_on_status(self):
        """
        Redireciona o utilizador para a tela correta com base no seu status.
        """
        status = self.user_profile.get("status")
        if status == "approved":
            # Obtém a instância do MainMenuView
            main_menu_frame = self.frames["MainMenuView"]
            # Atualiza as informações do utilizador na tela antes de exibi-la
            main_menu_frame.update_user_info(email=self.user_email,
                                             user_profile=self.user_profile,
                                             app_version=self.VERSION)
            self.show_frame("MainMenuView") # Exibe o menu principal
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        elif status == "unregistered":
            self.show_frame("RequestAccessView")
        else:
            messagebox.showerror("Erro de Acesso", f"Status desconhecido: {status}")
            self.perform_logout()

    def perform_logout(self):
        """
        Realiza o logout do utilizador, limpando a sessão e retornando à tela de login.
        """
        self.auth_service.logout()
        self.user_email = ""
        self.user_profile = {}
        self.frames["LoginView"].set_default_state()
        self.show_frame("LoginView")
        self.sheets_service.clear_all_cache()


    # --- MÉTODOS DE SERVIÇO (Pass-through para os serviços) ---

    def get_occurrences(self, force_refresh=False):
        return self.occurrence_service.get_all_occurrences_for_user(self.user_email, force_refresh)

    def get_all_occurrences_for_admin(self, force_refresh=False):
        return self.sheets_service.get_all_occurrences(force_refresh)

    def submit_occurrence(self, data, tests, attachment_path=None):
        reg_view = self.frames.get("RegistrationView")
        if reg_view:
            reg_view.set_submitting_state(True)

        def _submit():
            success, message = self.sheets_service.register_occurrence(self.user_email, data, tests, attachment_path)
            self.after(0, _handle_submit_result, success, message)

        def _handle_submit_result(success, message):
            if reg_view:
                reg_view.set_submitting_state(False)
                if success:
                    NotificationPopup(self, message="Ocorrência registrada com sucesso!", type="success")
                    reg_view.clear_form()
                else:
                    messagebox.showerror("Erro ao Registrar", message)

        threading.Thread(target=_submit, daemon=True).start()

    def submit_full_occurrence(self, title):
        """
        Wrapper para submeter uma ocorrência detalhada a partir da RegistrationView.
        Coleta os dados necessários e chama o método de submissão genérico.
        """
        # A RegistrationView armazena os testes no controller.
        # Idealmente, o estado deveria pertencer à view, mas isto resolve o problema atual.
        tests = getattr(self, 'testes_adicionados', [])
        data = {'title': title}
        
        # A RegistrationView atual não lida com anexos, então passamos None.
        self.submit_occurrence(data, tests, attachment_path=None)

    def submit_simple_call_occurrence(self, data):
        view = self.frames.get("SimpleCallView")
        if view:
            view.set_submitting_state(True)
        def _submit():
            success, message = self.occurrence_service.register_simple_call_occurrence(self.user_email, self.user_profile, data)
            self.after(0, self._handle_generic_submit_result, success, message, view)
        threading.Thread(target=_submit, daemon=True).start()

    def submit_equipment_occurrence(self, data, attachment_paths=None):
        view = self.frames.get("EquipmentView")
        if view:
            view.set_submitting_state(True)
        def _submit():
            user_credentials = self.auth_service.load_user_credentials()
            success, message = self.sheets_service.register_equipment_occurrence(user_credentials, self.user_email, data, attachment_paths or [])
            self.after(0, self._handle_generic_submit_result, success, message, view)
        threading.Thread(target=_submit, daemon=True).start()

    def _handle_generic_submit_result(self, success, message, view):
        if view:
            view.set_submitting_state(False)
        if success:
            NotificationPopup(self, message=message, type="success")
            if view:
                view.clear_form()
        else:
            messagebox.showerror("Erro ao Registrar", message)

    def show_occurrence_details(self, occurrence_id):
        """
        Mostra a tela de detalhes de uma ocorrência específica.
        Busca os dados de uma ocorrência e mostra a janela de detalhes (Toplevel).
        """
        # Importa a view aqui para evitar potenciais dependências circulares
        from views.main.occurrence_detail_view import OccurrenceDetailView

        occurrence_data = self.occurrence_service.get_occurrence_details(occurrence_id)
        if occurrence_data:
            # A OccurrenceDetailView é uma janela Toplevel, então é instanciada diretamente
            detail_window = OccurrenceDetailView(master=self, occurrence_data=occurrence_data)
        else:
            messagebox.showerror("Erro", f"Não foi possível encontrar os detalhes para a ocorrência {occurrence_id}.")

    def get_pending_requests(self):
        return self.user_service.get_pending_requests()

    def get_all_users(self, force_refresh=False):
        return self.user_service.get_all_users(force_refresh)

    def get_operator_list(self, force_refresh=False):
        return self.sheets_service.get_all_operators(force_refresh)

    def update_user_access(self, email, new_status):
        success, message = self.user_service.update_user_access(email, new_status)
        if success:
            NotificationPopup(self, message, type="success")
            self.frames["AccessManagementView"].load_access_requests()
        else:
            messagebox.showerror("Erro", message)

    def update_user_profiles_batch(self, changes):
        success, message = self.user_service.update_user_profiles_batch(changes)
        if success:
            NotificationPopup(self, message, type="success")
            self.frames["UserManagementView"].on_show(force_refresh=True)
        else:
            messagebox.showerror("Erro ao Atualizar", message)

    def update_occurrence_status_from_history(self, occurrence_id, new_status):
        """
        Atualiza o status de uma ocorrência a partir da tela de histórico.
        """
        success, message = self.sheets_service.update_occurrence_status(occurrence_id, new_status)
        if success:
            NotificationPopup(self, message, type="success")
            self.frames["HistoryView"].load_history()
        else:
            messagebox.showerror("Erro", message)
            self.frames["HistoryView"].load_history()

    def get_current_user_profile(self):
        """Retorna o perfil do utilizador atualmente logado."""
        return self.user_profile

    # --- LÓGICA DE ATUALIZAÇÃO ---
    def check_for_updates(self):
        """
        Verifica se há uma nova versão da aplicação disponível.
        """
        try:
            response = requests.get(self.VERSION_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("version")
            self.NEW_INSTALLER_DOWNLOAD_URL = data.get("url")

            if latest_version and self.NEW_INSTALLER_DOWNLOAD_URL:
                if latest_version > self.VERSION:
                    self.after(0, self.prompt_update, latest_version)
        except (requests.RequestException, ValueError) as e:
            print(f"REGTEL: Não foi possível verificar atualizações. Erro: {e}")

    def prompt_update(self, new_version):
        """
        Mostra uma mensagem a perguntar ao utilizador se deseja atualizar.
        """
        if messagebox.askyesno("Atualização Disponível",
                               f"Uma nova versão ({new_version}) está disponível.\n"
                               "Deseja baixar e instalar a atualização agora?"):
            self.initiate_update()

    def initiate_update(self):
        """
        Inicia o script de atualização 'updater.py' em um processo separado.
        """
        updater_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'services', 'updater.py'))

        if getattr(sys, '_MEIPASS', None): # type: ignore
            app_install_dir = os.path.dirname(sys.executable) # type: ignore
        else:
            app_install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        try:
            if sys.platform.startswith('win'):
                python_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                if not os.path.exists(python_exe):
                    python_exe = sys.executable
                subprocess.Popen([
                    python_exe,
                    updater_script_path,
                    self.NEW_INSTALLER_DOWNLOAD_URL,
                    app_install_dir
                ], shell=False, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen([
                    sys.executable,
                    updater_script_path,
                    self.NEW_INSTALLER_DOWNLOAD_URL,
                    app_install_dir
                ], shell=False)

            print("REGTEL: Iniciando processo de atualização. A aplicação será fechada.")
            self.quit()
        except Exception as e:
            messagebox.showerror("Erro de Atualização", f"Não foi possível iniciar o processo de atualização: {e}")
