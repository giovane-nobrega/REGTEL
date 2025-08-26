# ==============================================================================
# ARQUIVO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação (refatorado).
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import threading

# Importações dos Serviços
from services.auth_service import AuthService
from services.sheets_service import SheetsService
from services.occurrence_service import OccurrenceService
from services.user_service import UserService

# Importações das Views (com os novos caminhos)
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
    """ Controlador central da aplicação. """
    def __init__(self):
        super().__init__()
        self.title("Plataforma de Registro de Ocorrências (REGTEL)")
        self.geometry("900x750")
        self.minsize(800, 650)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Paleta de Cores
        self.PRIMARY_COLOR = "#00BFFF"
        self.ACCENT_COLOR = "#00CED1"
        self.BASE_COLOR = "#0A0E1A"
        self.TEXT_COLOR = "#FFFFFF"
        self.DANGER_COLOR = "#D32F2F"
        self.DANGER_HOVER_COLOR = "#B71C1C"
        self.GRAY_BUTTON_COLOR = "gray50"
        self.GRAY_HOVER_COLOR = "gray40"
        self.configure(fg_color=self.BASE_COLOR)

        # Injeção de Dependência dos Serviços
        self.auth_service = AuthService()
        self.sheets_service = SheetsService(self.auth_service)
        self.user_service = UserService(self.sheets_service)
        self.occurrence_service = OccurrenceService(self.sheets_service, self.auth_service)

        # Estado da Aplicação
        self.credentials = None
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.detail_window = None
        self.testes_adicionados = []
        self.editing_index = None
        self.operator_list = []

        # Configuração das Views
        container = ctk.CTkFrame(self, fg_color=self.BASE_COLOR)
        container.pack(fill="both", expand=True)
        self.frames = {}
        view_classes = {
            "LoginView": LoginView, "RequestAccessView": RequestAccessView, 
            "PendingApprovalView": PendingApprovalView, "MainMenuView": MainMenuView,
            "AdminDashboardView": AdminDashboardView, "HistoryView": HistoryView,
            "RegistrationView": RegistrationView, "SimpleCallView": SimpleCallView,
            "EquipmentView": EquipmentView, "AccessManagementView": AccessManagementView,
            "UserManagementView": UserManagementView
        }
        for name, F in view_classes.items():
            frame = F(parent=container, controller=self)
            self.frames[name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        self.current_frame = None
        self.previous_frame_name = None
        self.check_initial_login()

    def show_frame(self, page_name, from_view=None, mode="all"):
        """ Exibe uma tela específica da aplicação. """
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
        """ Exibe a janela de detalhes de uma ocorrência. """
        if self.detail_window and self.detail_window.winfo_exists():
            self.detail_window.focus()
            return
        occurrence_data = self.occurrence_service.get_occurrence_details(occurrence_id)
        if occurrence_data:
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

    def check_initial_login(self):
        """ Verifica se há uma sessão de login salva ao iniciar. """
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

    def load_secondary_data(self):
        """ Carrega dados secundários, como a lista de operadoras. """
        threading.Thread(target=self._load_operators_thread, daemon=True).start()

    def _load_operators_thread(self):
        self.operator_list = self.sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.after(0, self.frames["RegistrationView"].set_operator_suggestions, self.operator_list)

    def perform_login(self):
        """ Inicia o fluxo de login do usuário. """
        self.frames["LoginView"].set_loading_state("Aguarde... Abrindo o navegador para autenticação...")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = self.auth_service.run_login_flow()
        if creds:
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login falhou."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        """ Busca o perfil do usuário após o login. """
        self.user_email = str(self.auth_service.get_user_email(self.credentials))
        self.user_profile = self.user_service.get_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        """ Navega para a tela apropriada com base no status do usuário. """
        status = self.user_profile.get("status")
        if status == "approved":
            self.load_secondary_data()
            self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            self.show_frame("RequestAccessView")

    def perform_logout(self):
        """ Realiza o logout do usuário. """
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.show_frame("LoginView")

    def submit_access_request(self, *args):
        """ Envia uma solicitação de acesso. """
        self.user_service.submit_access_request(self.user_email, *args)
        self.show_frame("PendingApprovalView")

    def get_all_users(self, force_refresh=False):
        """ Obtém todos os usuários. """
        return self.user_service.get_all_users(force_refresh)

    def get_pending_requests(self):
        """ Obtém as solicitações de acesso pendentes. """
        return self.user_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        """ Atualiza o status de acesso de um usuário. """
        self.user_service.update_user_access(email, new_status)
        self.frames["AccessManagementView"].load_access_requests()

    def get_all_occurrences(self, force_refresh=False):
        """ Obtém todas as ocorrências visíveis para o usuário. """
        return self.occurrence_service.get_all_occurrences_for_user(self.user_email, force_refresh)

    def filter_occurrences(self, occurrences, filters):
        """ Delega a filtragem de ocorrências para o serviço. """
        return self.occurrence_service.filter_occurrences(occurrences, filters)

    def submit_simple_call_occurrence(self, form_data):
        """ Envia uma ocorrência de chamada simples. """
        self.frames["SimpleCallView"].set_submitting_state(True)
        threading.Thread(target=self._submit_occurrence, args=("SimpleCallView", self.occurrence_service.submit_simple_call, self.user_email, form_data), daemon=True).start()

    def _submit_occurrence(self, view_name, service_method, *args):
        """ Thread genérica para submissão de ocorrências. """
        success, message = service_method(*args)
        self.after(0, self._on_submission_finished, view_name, success, message)

    def _on_submission_finished(self, view_name, success, message):
        """ Callback executado após a submissão de uma ocorrência. """
        view = self.frames[view_name]
        if hasattr(view, 'set_submitting_state'):
            view.set_submitting_state(False)
        if success:
            NotificationPopup(self, message=message, type="success")
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Erro", message)