import customtkinter as ctk
import threading
from tkinter import messagebox
from customtkinter import filedialog

from services import auth_service, sheets_service
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.access_views import RequestAccessView, PendingApprovalView
from views.admin_dashboard_view import AdminDashboardView
from views.registration_view import RegistrationView
from views.simple_call_view import SimpleCallView
from views.equipment_view import EquipmentView
from views.history_view import HistoryView


class App(ctk.CTk):
    """
    Classe principal da aplicação. Atua como o controlador central.
    """

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

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
                  AdminDashboardView, RegistrationView, SimpleCallView, EquipmentView, HistoryView):
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

    def check_initial_login(self):
        threading.Thread(target=self.load_operators, daemon=True).start()
        
        self.credentials = auth_service.load_credentials()
        if self.credentials:
            self.frames["LoginView"].set_loading_state("Verificando credenciais...")
            threading.Thread(target=self._fetch_user_profile, daemon=True).start()
        else:
            self.show_frame("LoginView")

    def load_operators(self):
        self.operator_list = sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.frames["RegistrationView"].set_operator_suggestions(self.operator_list)

    def export_analysis_to_csv(self, data_list):
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                title="Salvar Relatório CSV"
            )
            if not filepath: return
            threading.Thread(
                target=self._write_csv_thread,
                args=(data_list, filepath),
                daemon=True
            ).start()
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Ocorreu um erro inesperado:\n{e}")

    def _write_csv_thread(self, data_list, filepath):
        success, message = sheets_service.write_to_csv(data_list, filepath)
        if success:
            self.after(0, lambda: messagebox.showinfo("Exportação Concluída", message))
        else:
            self.after(0, lambda: messagebox.showerror("Erro na Exportação", message))

    # ALTERAÇÃO AQUI: Nova função para obter a lista de empresas para o filtro
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
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail do Google."))
            self.after(0, self.perform_logout)
            return
        self.user_profile = sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        status = self.user_profile.get("status")
        if status == "approved":
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
        self.user_email = None
        self.credentials = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    # ALTERAÇÃO AQUI: A função agora aceita 'company_name'
    def submit_access_request(self, full_name, username, role, company_name=None):
        if not full_name or not username or not role:
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha todos os campos.")
            return
        sheets_service.request_access(self.user_email, full_name, username, role, company_name)
        messagebox.showinfo("Solicitação Enviada", "Sua solicitação de acesso foi enviada.")
        self.show_frame("PendingApprovalView")

    def get_pending_requests(self):
        return sheets_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        sheets_service.update_user_status(email, new_status)
        messagebox.showinfo("Sucesso", f"O acesso para {email} foi atualizado para '{new_status}'.")
        self.frames["AdminDashboardView"].load_access_requests()

    def get_all_occurrences(self, status_filter=None, role_filter=None, search_term=None):
        return sheets_service.get_all_occurrences_for_admin(status_filter, role_filter, search_term)

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        for occ_id, new_status in changes.items():
            sheets_service.update_occurrence_status(occ_id, new_status)
        messagebox.showinfo("Sucesso", f"{len(changes)} alterações de status foram salvas com sucesso.")
        self.frames["AdminDashboardView"].load_all_occurrences()

    def get_all_users(self):
        return sheets_service.get_all_users()

    def update_user_role(self, email, new_role):
        sheets_service.update_user_role(email, new_role)
        messagebox.showinfo("Sucesso", f"O perfil de {email} foi atualizado para '{new_role}'.")
        self.frames["AdminDashboardView"].load_all_users()

    def get_user_occurrences(self, search_term=None):
        return sheets_service.get_occurrences_by_user(self.credentials, self.user_email, search_term)

    def get_current_user_role(self):
        return self.user_profile.get("role")

    def submit_simple_call_occurrence(self, form_data):
        print("Submetendo ocorrência de chamada simples:", form_data)
        messagebox.showinfo("Sucesso", "Ocorrência de chamada simples registrada!")
        self.show_frame("MainMenuView")

    def submit_equipment_occurrence(self, data):
        print("Submetendo ocorrência de equipamento:", data)
        messagebox.showinfo("Sucesso", "Ocorrência de equipamento registrada!")
        self.show_frame("MainMenuView")

    def submit_full_occurrence(self, title):
        if not title:
            messagebox.showwarning("Campo Obrigatório", "O título da ocorrência é obrigatório.")
            return
        if len(self.testes_adicionados) < 3:
            messagebox.showwarning("Validação Falhou", "É necessário adicionar pelo menos 3 testes de ligação como evidência.")
            return
        view = self.frames["RegistrationView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_full_occurrence_thread, args=(title, self.testes_adicionados), daemon=True).start()

    def _submit_full_occurrence_thread(self, title, testes):
        sheets_service.register_full_occurrence(self.user_email, title, testes)
        self.after(0, self._on_full_occurrence_submitted)

    def _on_full_occurrence_submitted(self):
        messagebox.showinfo("Sucesso", "Ocorrência registrada com sucesso!")
        view = self.frames["RegistrationView"]
        view.set_submitting_state(False)
        self.show_frame("MainMenuView")
