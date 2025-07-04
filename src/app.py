# Ficheiro: src/app.py

import customtkinter as ctk
import threading
from tkinter import messagebox
from functools import partial

# As importações agora são diretas, pois 'main.py' configurou o caminho para a pasta 'src'.
# NOTA: Estes ficheiros de 'views' ainda precisam de ser criados.
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
    Classe principal da aplicação. Atua como o controlador central,
    gerindo o estado e a navegação entre as diferentes visualizações (telas).
    """
    def __init__(self):
        """Inicializa a janela principal, o estado da aplicação e as visualizações."""
        super().__init__()
        self.title("Plataforma de Registo de Ocorrências (Craft Quest)")
        self.geometry("850x750")
        self.minsize(750, 650)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- Variáveis de Estado da Aplicação ---
        self.credentials = None
        self.user_email = "A carregar..."
        self.user_profile = {}

        # --- Contentor Principal ---
        # Todas as visualizações serão colocadas dentro deste frame.
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        # --- Dicionário de Telas (Views) ---
        # Cada tela é uma classe de uma 'view' que é instanciada aqui.
        self.frames = {}
        for F in (LoginView, RequestAccessView, PendingApprovalView, MainMenuView, 
                  AdminDashboardView, RegistrationView, SimpleCallView, EquipmentView, HistoryView):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        # --- Inicialização ---
        self.check_initial_login()

    # =================================================================================
    # --- LÓGICA DE NAVEGAÇÃO E AUTENTICAÇÃO ---
    # =================================================================================

    def show_frame(self, page_name):
        """Eleva um frame (tela) para o topo, tornando-o visível."""
        frame = self.frames[page_name]
        # Chama o método on_show se a view o tiver, para carregar dados frescos.
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
            main_menu.update_user_info(self.user_email)
            main_menu.update_buttons(self.user_profile.get("role"))
            self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
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

    def submit_access_request(self, role):
        """Envia uma solicitação de acesso."""
        if not role:
            messagebox.showwarning("Campo Obrigatório", "Por favor, selecione o seu vínculo.")
            return
        sheets_service.request_access(self.user_email, role)
        messagebox.showinfo("Solicitação Enviada", "A sua solicitação de acesso foi enviada.")
        self.show_frame("PendingApprovalView")
        
    # =================================================================================
    # --- MÉTODOS DO CONTROLADOR (Pontes entre Views e Services) ---
    # =================================================================================
    
    def get_pending_requests(self):
        """Busca as solicitações de acesso pendentes."""
        return sheets_service.get_pending_requests()
        
    def update_user_access(self, email, new_status):
        """Atualiza o status de acesso de um utilizador."""
        sheets_service.update_user_status(email, new_status)
        messagebox.showinfo("Sucesso", f"O acesso para {email} foi atualizado para '{new_status}'.")
        # Pede ao dashboard para recarregar a lista de acessos
        self.frames["AdminDashboardView"].load_access_requests()

    def get_all_occurrences(self):
        """Busca todas as ocorrências para o admin."""
        return sheets_service.get_all_occurrences_for_admin()
        
    def save_occurrence_status_changes(self, changes):
        """Salva as alterações de status feitas pelo admin."""
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
            
        for occ_id, new_status in changes.items():
            sheets_service.update_occurrence_status(occ_id, new_status)
        
        messagebox.showinfo("Sucesso", f"{len(changes)} alterações de status foram salvas com sucesso.")
        self.frames["AdminDashboardView"].load_all_occurrences()
