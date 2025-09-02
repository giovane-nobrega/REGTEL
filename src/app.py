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
from builtins import super, print, Exception, hasattr, len, max, range, int, str, dict, open

# --- Imports de serviços e utils (caminhos inalterados) ---
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
from views.components.autocomplete_widget import AutocompleteEntry
from views.components.notification_popup import NotificationPopup


class App(ctk.CTk):
    def __init__(self):
        # --- Configuração do Logging ---
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "REGTEL_Logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file_path = os.path.join(log_dir, "app_debug.log")

        try:
            self._log_file = open(self.log_file_path, 'w', encoding='utf-8')
            sys.stdout = self._log_file
            sys.stderr = self._log_file
            print(f"--- REGTEL Debug Log Iniciado em: {self.log_file_path} ---")
        except Exception as e:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print(f"ERRO: Não foi possível iniciar o log para o ficheiro: {self.log_file_path}. Detalhes: {e}")
            messagebox.showerror("Erro de Log", f"Não foi possível iniciar o log da aplicação. Detalhes: {e}")

        # --- Inicialização da Janela Principal ---
        super().__init__()
        self.title("Plataforma de Registro de Ocorrências (REGTEL)")
        self.geometry("900x750")
        self.minsize(800, 650)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- Cores da Aplicação ---
        self.PRIMARY_COLOR = "#00BFFF"
        self.ACCENT_COLOR = "#00CED1"
        self.BASE_COLOR = "#0A0E1A"
        self.TEXT_COLOR = "#FFFFFF"
        self.DANGER_COLOR = "#D32F2F"
        self.DANGER_HOVER_COLOR = "#B71C1C"
        self.GRAY_BUTTON_COLOR = "gray50"
        self.GRAY_HOVER_COLOR = "gray40"

        self.configure(fg_color=self.BASE_COLOR)

        # A instância da App é o controlador principal
        self.controller = self 

        # --- Configuração do Ícone ---
        if getattr(sys, '_MEIPASS', None): # type: ignore
            base_path = sys._MEIPASS # type: ignore
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        icon_path = os.path.join(base_path, 'icon.ico')

        try:
            self.iconbitmap(icon_path)
        except tk.TclError as e:
            print(f"Aviso: Não foi possível carregar o ícone da janela em '{icon_path}'. Erro: {e}")
        except Exception as e:
            print(f"Aviso: Ocorreu um erro inesperado ao definir o ícone da janela: {e}")

        # --- Inicialização dos Serviços e Variáveis de Estado ---
        self.auth_service = AuthService()
        self.sheets_service = SheetsServiceClass(self.auth_service)
        self.occurrence_service = OccurrenceService(self.sheets_service, self.auth_service)
        self.user_service = UserService(self.sheets_service)

        self.credentials = None
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.detail_window = None
        self.testes_adicionados = []
        self.editing_index = None
        self.operator_list = []
        self.occurrences_cache = None
        self.users_cache = None

        # --- Container Principal e Gestão de Frames (Telas) ---
        container = ctk.CTkFrame(self, fg_color=self.BASE_COLOR)
        container.pack(fill="both", expand=True)

        self.frames = {}
        view_classes = (
            LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
            AdminDashboardView, HistoryView, RegistrationView, SimpleCallView,
            EquipmentView, AccessManagementView, UserManagementView
        )

        self.current_frame = None
        self.previous_frame_name = None

        for F in view_classes:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        self.check_initial_login()

        # --- Configurações de Atualização Automática ---
        self.CURRENT_APP_VERSION = "1.0.2"
        self.REMOTE_VERSION_URL = "https://raw.githubusercontent.com/giovane-nobrega/REGTEL/master/updates/version.txt"
        self.NEW_INSTALLER_DOWNLOAD_URL = "https://github.com/giovane-nobrega/REGTEL/releases/download/v1.0.2/REGTEL_Installer_1.0.2.exe"

        self.after(2000, lambda: threading.Thread(target=self.check_for_updates, daemon=True).start())
        
    def show_frame(self, page_name, from_view=None, mode="all"):
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
        occurrence_data = self.occurrence_service.get_occurrence_details(occurrence_id)
        if occurrence_data:
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

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

    def load_secondary_data(self):
        threading.Thread(target=self._load_operators_thread, daemon=True).start()

    def _load_operators_thread(self):
        self.operator_list = self.sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.after(0, self.frames["RegistrationView"].set_operator_suggestions, self.operator_list)

    def perform_login(self):
        self.frames["LoginView"].set_loading_state("Aguarde... Uma janela do navegador foi aberta para autenticação. Por favor, complete o login e retorne ao aplicativo.")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = self.auth_service.run_login_flow()
        if creds:
            self.auth_service.save_user_credentials(creds)
            self.credentials = creds
            self.after(0, self.deiconify)
            self.after(0, self.lift)
            self.after(0, self.focus_force)
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou. Por favor, tente novamente."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        self.user_email = str(self.auth_service.get_user_email(self.credentials))
        if "Erro" in self.user_email or not self.user_email.strip():
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail. Por favor, tente novamente ou contacte o suporte."))
            self.after(0, self.perform_logout)
            return
        self.user_profile = self.user_service.get_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        status = self.user_profile.get("status")
        main_group = self.user_profile.get("main_group")
        sub_group = self.user_profile.get("sub_group")
        if status == "approved":
            self.load_secondary_data()
            main_menu = self.frames["MainMenuView"]
            main_menu.update_user_info(self.user_email, self.user_profile, self.CURRENT_APP_VERSION)
            if main_group == "67_TELECOM" and sub_group == "SUPER_ADMIN":
                self.show_frame("AdminDashboardView")
                return
            self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            self.frames["RequestAccessView"].on_show()
            self.show_frame("RequestAccessView")

    def perform_logout(self):
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    def submit_access_request(self, full_name, username, main_group, sub_group, company_name=None):
        if not self.user_email or self.user_email.strip() == "" or "Erro" in self.user_email:
            messagebox.showerror("Erro Crítico", "Não foi possível obter seu e-mail. Por favor, tente fazer login novamente.")
            self.perform_logout()
            return

        success, message = self.user_service.submit_access_request(self.user_email, full_name, username, main_group, sub_group, company_name)
        if success:
            NotificationPopup(self, message="Solicitação enviada com sucesso! Aguarde aprovação.", type="success")
            self.show_frame("PendingApprovalView")
        else:
            if "já existe para este e-mail" in message:
                messagebox.showerror("E-mail Já Registrado", "Este e-mail já está registado em nosso sistema. Por favor, utilize outro e-mail ou entre em contacto com o administrador para assistência.")
            else:
                messagebox.showerror("Erro ao Enviar Solicitação", f"Não foi possível enviar sua solicitação de acesso: {message}\nPor favor, verifique seus dados e tente novamente.")

    def get_all_occurrences(self, force_refresh=False, exclude_statuses=None):
        occurrences = self.occurrence_service.get_all_occurrences_for_user(self.user_email, force_refresh)
        if exclude_statuses:
            exclude_statuses_upper = [s.upper() for s in exclude_statuses]
            return [occ for occ in occurrences if occ.get('Status', '').upper() not in exclude_statuses_upper]
        return occurrences

    def get_all_users(self, force_refresh=False):
        return self.user_service.get_all_users(force_refresh)

    def get_pending_requests(self):
        return self.user_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        success, message = self.user_service.update_user_access(email, new_status)
        if success:
            if new_status == 'approved':
                NotificationPopup(self, message=f"O acesso para {email} foi aprovado com sucesso.", type="success")
            else:
                NotificationPopup(self, message=f"O acesso para {email} foi rejeitado.", type="info")
            self.frames["AccessManagementView"].load_access_requests()
        else:
            messagebox.showerror("Erro ao Atualizar", f"Ocorreu um erro ao atualizar o acesso: {message}")

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        success, message = self.sheets_service.batch_update_occurrence_statuses(changes)
        if success:
            self.occurrences_cache = None
            NotificationPopup(self, message=f"Os status de {len(changes)} ocorrência(s) foram salvos com sucesso.", type="success")
            if "AdminDashboardView" in self.frames and hasattr(self.frames["AdminDashboardView"], '_occurrences_tab_initialized') and self.frames["AdminDashboardView"]._occurrences_tab_initialized:
                self.frames["AdminDashboardView"].load_all_occurrences(force_refresh=True)
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
        else:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar as alterações de status: {message}")

    def update_user_profile(self, changes: dict):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")
            return
        success, message = self.user_service.update_user_profiles_batch(changes)
        if success:
            NotificationPopup(self, message=f"{len(changes)} perfil(is) de usuário foram atualizados com sucesso.", type="success")
            self.frames["UserManagementView"].load_all_users(force_refresh=True)
        else:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao atualizar os perfis: {message}")

    def get_user_occurrences(self):
        return self.get_all_occurrences()

    def get_current_user_profile(self):
        return self.user_service.get_user_status(self.user_email)

    def submit_simple_call_occurrence(self, form_data):
        view = self.frames["SimpleCallView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_simple_call_thread, args=(form_data,), daemon=True).start()

    def _submit_simple_call_thread(self, form_data):
        success, message = self.sheets_service.register_simple_call_occurrence(self.user_email, form_data)
        self.after(0, self._on_submission_finished, "SimpleCallView", success, message)

    def submit_equipment_occurrence(self, data, attachment_paths=None):
        view = self.frames["EquipmentView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_equipment_thread, args=(data, attachment_paths), daemon=True).start()

    def _submit_equipment_thread(self, data, attachment_paths):
        success, message = self.sheets_service.register_equipment_occurrence(self.credentials, self.user_email, data, attachment_paths)
        self.after(0, self._on_submission_finished, "EquipmentView", success, message)

    def submit_full_occurrence(self, title):
        profile = self.get_current_user_profile()
        main_group = profile.get("main_group")
        if not title:
            messagebox.showwarning("Campo Obrigatório", "O título da ocorrência é obrigatório.")
            return
        if main_group == 'PARTNER' and len(self.testes_adicionados) < 3:
            messagebox.showwarning("Validação Falhou", "É necessário adicionar pelo menos 3 testes para parceiros.")
            return
        view = self.frames["RegistrationView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_full_occurrence_thread, args=(title, self.testes_adicionados.copy()), daemon=True).start()

    def _submit_full_occurrence_thread(self, title, testes):
        success, message = self.sheets_service.register_full_occurrence(self.user_email, title, testes)
        self.after(0, self._on_submission_finished, "RegistrationView", success, message)

    def _on_submission_finished(self, view_name, success, message):
        view = self.frames[view_name]
        if hasattr(view, 'set_submitting_state'):
            view.set_submitting_state(False)
        if success:
            self.occurrences_cache = None
            NotificationPopup(self, message=message, type="success")
            if hasattr(view, 'on_show'):
                 view.on_show()
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Ocorreu um Erro", f"Não foi possível completar a operação: {message}\nPor favor, tente novamente.")

    def update_occurrence_status_from_history(self, occurrence_id, new_status):
        success, message = self.sheets_service.update_occurrence_status(occurrence_id, new_status)
        if success:
            self.occurrences_cache = None
            NotificationPopup(self, message=f"Status da ocorrência {occurrence_id} atualizado para '{new_status}'.", type="success")
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
            if "AdminDashboardView" in self.frames and hasattr(self.frames["AdminDashboardView"], '_occurrences_tab_initialized') and self.frames["AdminDashboardView"]._occurrences_tab_initialized:
                self.frames["AdminDashboardView"].load_all_occurrences(force_refresh=True)
        else:
            messagebox.showerror("Erro", f"Não foi possível atualizar o status da ocorrência: {message}")

    def check_for_updates(self):
        try:
            response = requests.get(self.REMOTE_VERSION_URL, timeout=5)
            response.raise_for_status()
            remote_version = response.text.strip()
            if remote_version and self._compare_versions(remote_version, self.CURRENT_APP_VERSION) > 0:
                self.after(0, lambda: self._prompt_for_update(remote_version))
            else:
                print("REGTEL: Nenhuma atualização disponível ou já está na versão mais recente.")
        except requests.exceptions.RequestException as e:
            print(f"REGTEL: Erro ao verificar atualizações: {e}")
        except Exception as e:
            print(f"REGTEL: Erro inesperado na verificação de atualização: {e}")

    def _compare_versions(self, version1, version2):
        v1_parts = [int(p) for p in version1.split('.')]
        v2_parts = [int(p) for p in version2.split('.')]
        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            if p1 > p2:
                return 1
            if p1 < p2:
                return -1
        return 0

    def _prompt_for_update(self, remote_version):
        if messagebox.askyesno(
            "Atualização Disponível",
            f"Uma nova versão do REGTEL ({remote_version}) está disponível!\n"
            "Deseja descarregar e instalar a atualização agora?\n\n"
            "A aplicação será fechada para iniciar o processo de atualização."
        ):
            self.initiate_update()
        else:
            NotificationPopup(self, message="Atualização adiada. Pode verificar novamente mais tarde.", type="info")

    def initiate_update(self):
        if getattr(sys, '_MEIPASS', None): # type: ignore
            updater_script_path = os.path.join(sys._MEIPASS, 'services', 'updater.py') # type: ignore
        else:
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
            print(f"REGTEL: Erro ao iniciar o updater: {e}")
