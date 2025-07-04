import customtkinter as ctk
import threading
from tkinter import messagebox

# Importações diretas, pois 'main.py' configurou o caminho.
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
        self.title("Plataforma de Registo de Ocorrências (Craft Quest)")
        self.geometry("900x750") # Aumentei a largura para acomodar o novo dashboard
        self.minsize(800, 650)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.credentials = None
        self.user_email = "A carregar..."
        self.user_profile = {}
        # Variáveis de estado para o formulário de registo detalhado
        self.testes_adicionados = [] 
        self.editing_index = None

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
        """Eleva um frame (tela) para o topo, tornando-o visível."""
        frame = self.frames[page_name]
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()

    def check_initial_login(self):
        """Verifica as credenciais no início da aplicação."""
        self.credentials = auth_service.load_credentials()
        if self.credentials:
            self.frames["LoginView"].set_loading_state("A verificar credenciais...")
            threading.Thread(target=self._fetch_user_profile, daemon=True).start()
        else:
            self.show_frame("LoginView")

    def perform_login(self):
        """Inicia o fluxo de login do Google."""
        self.frames["LoginView"].set_loading_state("Aguarde... A abrir o navegador")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        """Executa o login numa thread separada."""
        creds = auth_service.run_login_flow()
        if creds:
            auth_service.save_credentials(creds)
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, self._login_failed)

    def _fetch_user_profile(self):
        """Busca o perfil do utilizador."""
        self.user_email = auth_service.get_user_email(self.credentials)
        if "Erro" in self.user_email:
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail do Google."))
            self.after(0, self.perform_logout)
            return
        
        self.user_profile = sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        """Navega para a tela correta com base no status do utilizador."""
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
        """Lida com falhas no login."""
        messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou.")
        self.frames["LoginView"].set_default_state()

    def perform_logout(self):
        """Realiza o logout do utilizador."""
        auth_service.logout()
        self.user_email = None
        self.credentials = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    def submit_access_request(self, full_name, username, role):
        """Envia uma nova solicitação de acesso."""
        if not full_name or not username or not role:
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha todos os campos.")
            return
        sheets_service.request_access(self.user_email, full_name, username, role)
        messagebox.showinfo("Solicitação Enviada", "A sua solicitação de acesso foi enviada.")
        self.show_frame("PendingApprovalView")
        
    # --- Métodos do Controlador (Pontes entre Views e Services) ---
    
    def get_pending_requests(self):
        return sheets_service.get_pending_requests()
        
    def update_user_access(self, email, new_status):
        sheets_service.update_user_status(email, new_status)
        messagebox.showinfo("Sucesso", f"O acesso para {email} foi atualizado para '{new_status}'.")
        self.frames["AdminDashboardView"].load_access_requests()

    def get_all_occurrences(self, status_filter=None):
        """Busca todas as ocorrências para o admin, com filtro opcional."""
        return sheets_service.get_all_occurrences_for_admin(status_filter)
        
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

    def get_user_occurrences(self):
        return sheets_service.get_occurrences_by_user(self.credentials, self.user_email)