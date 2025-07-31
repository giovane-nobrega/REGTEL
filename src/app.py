import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog

from services import auth_service, sheets_service
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.access_views import RequestAccessView, PendingApprovalView
from views.admin_dashboard_view import AdminDashboardView
from views.registration_view import RegistrationView
from views.simple_call_view import SimpleCallView
from views.equipment_view import EquipmentView
from views.history_view import HistoryView
from views.occurrence_detail_view import OccurrenceDetailView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Plataforma de Registro de Ocorrências (Craft Quest)")
        self.geometry("900x750")
        self.minsize(800, 650)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.credentials = None 
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.testes_adicionados = []
        self.editing_index = None
        self.operator_list = []
        self.detail_window = None

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        view_classes = (LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
                        AdminDashboardView, RegistrationView, SimpleCallView, EquipmentView, HistoryView)
        
        for F in view_classes:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        self.check_initial_login()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()

    def show_occurrence_details(self, occurrence_id):
        if self.detail_window is not None and self.detail_window.winfo_exists():
            self.detail_window.focus()
            return
        
        occurrence_data = sheets_service.get_occurrence_by_id(occurrence_id)
        if occurrence_data:
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

    def check_initial_login(self):
        self.frames["LoginView"].set_loading_state("Verificando credenciais...")
        threading.Thread(target=self._check_initial_login_thread, daemon=True).start()

    def _check_initial_login_thread(self):
        creds = auth_service.load_credentials()
        if creds:
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, self.frames["LoginView"].set_default_state)
            self.after(0, self.show_frame, "LoginView")

    def load_secondary_data(self):
        threading.Thread(target=self._load_operators_thread, daemon=True).start()

    def _load_operators_thread(self):
        self.operator_list = sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.after(0, self.frames["RegistrationView"].set_operator_suggestions, self.operator_list)

    def export_analysis_to_csv(self, data_list):
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")], title="Salvar Relatório CSV"
            )
            if not filepath: return
            threading.Thread(target=self._write_csv_thread, args=(data_list, filepath), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Ocorreu um erro inesperado:\n{e}")

    def _write_csv_thread(self, data_list, filepath):
        success, message = sheets_service.write_to_csv(data_list, filepath)
        if success:
            self.after(0, lambda: messagebox.showinfo("Exportação Concluída", message))
        else:
            self.after(0, lambda: messagebox.showerror("Erro na Exportação", message))

    def get_partner_companies(self):
        return sheets_service.get_all_partner_companies()

    def perform_login(self):
        self.frames["LoginView"].set_loading_state("Aguarde... Abrindo o navegador")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = auth_service.run_login_flow()
        if creds:
            auth_service.save_credentials(creds)
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, self._login_failed)

    def _fetch_user_profile(self):
        self.user_email = auth_service.get_user_email(self.credentials)
        if "Erro" in self.user_email:
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail."))
            self.after(0, self.perform_logout)
            return
        
        self.user_profile = sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        status = self.user_profile.get("status")
        if status == "approved":
            self.load_secondary_data()
            main_menu = self.frames["MainMenuView"]
            main_menu.update_user_info(self.user_email, self.user_profile.get("username", ""))
            main_menu.update_buttons(self.user_profile.get("role"))
            self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            self.frames["RequestAccessView"].on_show()
            self.show_frame("RequestAccessView")

    def _login_failed(self):
        messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou.")
        self.frames["LoginView"].set_default_state()

    def perform_logout(self):
        auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    def submit_access_request(self, full_name, username, role, company_name=None):
        role_map = {"Prefeitura": "prefeitura", "Parceiro": "partner", "Colaboradores 67": "telecom_user"}
        internal_role = role_map.get(role, "unknown")
        if not all([full_name, username, role]):
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha todos os campos.")
            return
        success, message = sheets_service.request_access(self.user_email, full_name, username, internal_role, company_name)
        messagebox.showinfo("Solicitação", message)
        if success:
            self.show_frame("PendingApprovalView")

    def get_pending_requests(self):
        return sheets_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        sheets_service.update_user_status(email, new_status)
        messagebox.showinfo("Sucesso", f"O acesso para {email} foi atualizado.")
        self.frames["AdminDashboardView"].load_access_requests()

    def get_all_occurrences(self, status_filter=None, role_filter=None, search_term=None):
        return sheets_service.get_all_occurrences(status_filter, role_filter, search_term)

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        for occ_id, new_status in changes.items():
            sheets_service.update_occurrence_status(occ_id, new_status)
        messagebox.showinfo("Sucesso", f"{len(changes)} alterações foram salvas.")
        self.frames["AdminDashboardView"].load_all_occurrences()

    def get_all_users(self):
        return sheets_service.get_all_users()

    def update_user_profile(self, email, new_role, new_company=None):
        sheets_service.update_user_profile(email, new_role, new_company)

    def get_user_occurrences(self, search_term=None):
        # --- ALTERAÇÃO AQUI: Passa o e-mail do utilizador atual ---
        # A função de serviço irá buscar o perfil mais recente a partir do e-mail.
        return sheets_service.get_occurrences_by_user(self.user_email, search_term)
        # --- FIM DA ALTERAÇÃO ---

    def get_current_user_role(self):
        # Busca o perfil mais recente para garantir que a role está atualizada
        latest_profile = sheets_service.check_user_status(self.user_email)
        return latest_profile.get("role")

    def submit_simple_call_occurrence(self, form_data):
        view = self.frames["SimpleCallView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_simple_call_thread, args=(form_data,), daemon=True).start()

    def _submit_simple_call_thread(self, form_data):
        success, message = sheets_service.register_simple_call_occurrence(self.user_email, form_data)
        self.after(0, self._on_submission_finished, "SimpleCallView", success, message)

    def submit_equipment_occurrence(self, data, attachment_paths=None):
        view = self.frames["EquipmentView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_equipment_thread, args=(data, attachment_paths), daemon=True).start()

    def _submit_equipment_thread(self, data, attachment_paths):
        success, message = sheets_service.register_equipment_occurrence(self.credentials, self.user_email, data, attachment_paths)
        self.after(0, self._on_submission_finished, "EquipmentView", success, message)

    def submit_full_occurrence(self, title):
        role = self.get_current_user_role()
        if not title:
            messagebox.showwarning("Campo Obrigatório", "O título da ocorrência é obrigatório.")
            return
        if role == 'partner' and len(self.testes_adicionados) < 3:
            messagebox.showwarning("Validação Falhou", "É necessário adicionar pelo menos 3 testes.")
            return
        
        view = self.frames["RegistrationView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_full_occurrence_thread, args=(title, self.testes_adicionados.copy()), daemon=True).start()

    def _submit_full_occurrence_thread(self, title, testes):
        success, message = sheets_service.register_full_occurrence(self.user_email, title, testes)
        self.after(0, self._on_submission_finished, "RegistrationView", success, message)

    def _on_submission_finished(self, view_name, success, message):
        view = self.frames[view_name]
        if hasattr(view, 'set_submitting_state'):
            view.set_submitting_state(False)

        if success:
            messagebox.showinfo("Sucesso", message)
            if hasattr(view, 'on_show'):
                 view.on_show()
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Falha no Registro", message)
